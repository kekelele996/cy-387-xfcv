"""报修分级响应、接单、超时升级的核心测试。"""
import threading
from datetime import timedelta
from unittest import skipUnless

from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app.apps.repair.models import RepairStaff, RepairTicket, TicketEvent
from app.apps.repair.services import (
    accept_ticket,
    complete_ticket,
    create_ticket,
    escalate_overdue_tickets,
    escalate_ticket,
)
from app.apps.repair.services.sla import get_response_limit_minutes
from app.utils.errors import BusinessError


class SLATestCase(TestCase):
    def test_response_limit_is_tiered(self):
        """水电、门锁 30 分钟；管道、家电、其他 4 小时。"""
        self.assertEqual(get_response_limit_minutes('水电'), 30)
        self.assertEqual(get_response_limit_minutes('门锁'), 30)
        for fault_type in ('管道', '家电', '其他'):
            self.assertEqual(get_response_limit_minutes(fault_type), 240)

    def test_create_ticket_sets_deadline(self):
        ticket = create_ticket(fault_type='水电', description='跳闸')
        self.assertEqual(ticket.status, '待响应')
        self.assertEqual(ticket.response_deadline - ticket.created_at, timedelta(minutes=30))
        self.assertTrue(ticket.events.filter(event_type='提交').exists())


class AcceptTicketTestCase(TestCase):
    def setUp(self):
        self.staff_a = RepairStaff.objects.create(name='甲')
        self.staff_b = RepairStaff.objects.create(name='乙')

    def test_accept_records_assignee_and_time(self):
        ticket = create_ticket(fault_type='管道', description='漏水')
        updated = accept_ticket(ticket.id, self.staff_a.id)
        self.assertEqual(updated.status, '处理中')
        self.assertEqual(updated.assignee_id, self.staff_a.id)
        self.assertIsNotNone(updated.accepted_at)
        self.assertTrue(updated.events.filter(event_type='接单', operator=self.staff_a).exists())

    def test_duplicate_accept_rejected(self):
        ticket = create_ticket(fault_type='水电', description='没电')
        accept_ticket(ticket.id, self.staff_a.id)
        with self.assertRaises(BusinessError):
            accept_ticket(ticket.id, self.staff_b.id)
        ticket.refresh_from_db()
        self.assertEqual(ticket.assignee_id, self.staff_a.id)
        self.assertEqual(ticket.events.filter(event_type='接单').count(), 1)

    def test_complete_requires_assignee(self):
        ticket = create_ticket(fault_type='家电', description='坏了')
        with self.assertRaises(BusinessError):
            complete_ticket(ticket.id, self.staff_a.id)
        accept_ticket(ticket.id, self.staff_a.id)
        with self.assertRaises(BusinessError):
            complete_ticket(ticket.id, self.staff_b.id)
        updated = complete_ticket(ticket.id, self.staff_a.id)
        self.assertEqual(updated.status, '已完成')
        self.assertIsNotNone(updated.completed_at)


class EscalationTestCase(TestCase):
    def setUp(self):
        self.staff_a = RepairStaff.objects.create(name='甲')
        self.staff_b = RepairStaff.objects.create(name='乙')
        self.staff_c = RepairStaff.objects.create(name='丙')

    def _backdated_ticket(self, fault_type, minutes_ago, **kwargs):
        now = timezone.now()
        limit = get_response_limit_minutes(fault_type)
        created = now - timedelta(minutes=minutes_ago)
        return RepairTicket.objects.create(
            fault_type=fault_type, description='故障',
            response_deadline=created + timedelta(minutes=limit),
            created_at=created, **kwargs,
        )

    def test_escalation_requires_overdue(self):
        ticket = self._backdated_ticket('水电', 10)
        with self.assertRaises(BusinessError):
            escalate_ticket(ticket.id)
        ticket.refresh_from_db()
        self.assertIsNone(ticket.assignee_id)
        self.assertFalse(ticket.escalated)

    def test_escalation_only_once(self):
        ticket = self._backdated_ticket('水电', 45)
        escalate_ticket(ticket.id)
        with self.assertRaises(BusinessError):
            escalate_ticket(ticket.id)
        ticket.refresh_from_db()
        self.assertTrue(ticket.escalated)
        self.assertEqual(ticket.events.filter(event_type='升级').count(), 1)

    def test_escalation_picks_least_loaded(self):
        # 甲有 2 个未完成工单，乙有 1 个，丙没有 → 超时工单应转派给丙
        for _ in range(2):
            accept_ticket(create_ticket(fault_type='水电', description='x').id, self.staff_a.id)
        accept_ticket(create_ticket(fault_type='家电', description='y').id, self.staff_b.id)
        ticket = self._backdated_ticket('门锁', 45)
        escalate_ticket(ticket.id)
        ticket.refresh_from_db()
        self.assertEqual(ticket.assignee_id, self.staff_c.id)
        event = ticket.events.get(event_type='升级')
        self.assertEqual(event.to_assignee_id, self.staff_c.id)
        self.assertIsNone(event.from_assignee_id)

    def test_scan_escalates_all_overdue_once(self):
        overdue_1 = self._backdated_ticket('水电', 40)
        overdue_2 = self._backdated_ticket('管道', 300)
        fresh = self._backdated_ticket('水电', 5)
        escalated = escalate_overdue_tickets()
        escalated_ids = {t.id for t in escalated}
        self.assertEqual(escalated_ids, {overdue_1.id, overdue_2.id})
        # 再次扫描不会重复升级
        self.assertEqual(escalate_overdue_tickets(), [])
        fresh.refresh_from_db()
        self.assertIsNone(fresh.assignee_id)

    def test_escalation_rollback_on_no_staff(self):
        ticket = self._backdated_ticket('水电', 45)
        RepairStaff.objects.update(is_active=False)
        with self.assertRaises(BusinessError):
            escalate_ticket(ticket.id)
        ticket.refresh_from_db()
        # 全部不变：处理人、升级标记、事件
        self.assertIsNone(ticket.assignee_id)
        self.assertFalse(ticket.escalated)
        self.assertFalse(ticket.events.filter(event_type='升级').exists())


class TicketAPITestCase(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.staff = RepairStaff.objects.create(name='甲')

    def test_create_list_filter_overdue(self):
        fresh = create_ticket(fault_type='水电', description='新工单')
        now = timezone.now()
        overdue = RepairTicket.objects.create(
            fault_type='门锁', description='超时工单',
            response_deadline=now - timedelta(minutes=15),
            created_at=now - timedelta(minutes=45),
        )
        TicketEvent.objects.create(ticket=overdue, event_type='提交')

        resp = self.client_api.get('/api/repair/tickets/?status=overdue')
        self.assertEqual(resp.status_code, 200)
        ids = [item['id'] for item in resp.json()]
        self.assertIn(overdue.id, ids)
        self.assertNotIn(fresh.id, ids)

        resp = self.client_api.get('/api/repair/tickets/?status=pending')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(fresh.id, [item['id'] for item in resp.json()])

    def test_accept_and_escalate_api_flow(self):
        ticket = create_ticket(fault_type='水电', description='待接单')
        resp = self.client_api.post(
            f'/api/repair/tickets/{ticket.id}/accept/', {'staffId': self.staff.id}, format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], '处理中')

        overdue = RepairTicket.objects.create(
            fault_type='门锁', description='超时',
            response_deadline=timezone.now() - timedelta(minutes=1),
        )
        resp = self.client_api.post(f'/api/repair/tickets/{overdue.id}/escalate/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['assigneeId'], self.staff.id)
        # 再次升级返回冲突
        resp = self.client_api.post(f'/api/repair/tickets/{overdue.id}/escalate/')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['code'], 'REPAIR_ALREADY_ESCALATED')

    def test_invalid_fault_type_returns_standard_error(self):
        resp = self.client_api.post(
            '/api/repair/tickets/', {'faultType': '不存在', 'description': 'x'}, format='json',
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertFalse(body['success'])
        self.assertIn('code', body)


@skipUnless(connection.vendor == 'postgresql', '并发行锁行为仅在 PostgreSQL 下验证')
class EscalationConcurrencyTestCase(TransactionTestCase):
    """两个线程同时升级同一工单：恰好一次成功、一次被拒，绝不重复转派。"""

    def test_concurrent_escalation_succeeds_exactly_once(self):
        RepairStaff.objects.create(name='甲')
        RepairStaff.objects.create(name='乙')
        now = timezone.now()
        ticket = RepairTicket.objects.create(
            fault_type='水电', description='并发超时工单',
            response_deadline=now - timedelta(minutes=1),
            created_at=now - timedelta(minutes=40),
        )
        results = []

        def worker():
            try:
                escalate_ticket(ticket.id)
                results.append('ok')
            except BusinessError as exc:
                results.append(f'error:{exc.code}')
            finally:
                connection.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sorted(results).count('ok'), 1)
        ticket.refresh_from_db()
        self.assertTrue(ticket.escalated)
        self.assertEqual(TicketEvent.objects.filter(ticket=ticket, event_type='升级').count(), 1)
