"""演示数据：物业人员与覆盖各状态的报修工单。"""
from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def seed_demo_data(apps, schema_editor):
    RepairStaff = apps.get_model('repair', 'RepairStaff')
    RepairTicket = apps.get_model('repair', 'RepairTicket')
    TicketEvent = apps.get_model('repair', 'TicketEvent')

    # 测试库不灌入演示数据：PostgreSQL 测试库名为 test_ 前缀，SQLite 测试库为内存库
    conn = schema_editor.connection
    db_name = str(conn.settings_dict.get('NAME', ''))
    is_test_db = db_name.startswith('test') or conn.vendor == 'sqlite' and 'mode=memory' in db_name
    if is_test_db or RepairStaff.objects.exists():
        return

    staff = [
        RepairStaff.objects.create(name='王建国', phone='13900000001'),
        RepairStaff.objects.create(name='李秀兰', phone='13900000002'),
        RepairStaff.objects.create(name='张师傅', phone='13900000003'),
    ]
    now = timezone.now()

    def make_ticket(*, fault_type, minutes_ago, status='待响应', assignee=None,
                    escalated=False, description='', submitter='住户'):
        limit = {'水电': 30, '门锁': 30, '管道': 240, '家电': 240, '其他': 240}[fault_type]
        created = now - timedelta(minutes=minutes_ago)
        return RepairTicket.objects.create(
            fault_type=fault_type,
            description=description or f'{fault_type}故障，请尽快上门处理',
            submitter_name=submitter,
            status=status,
            assignee=assignee,
            response_deadline=created + timedelta(minutes=limit),
            accepted_at=now - timedelta(minutes=max(minutes_ago - 5, 0)) if status in ('处理中', '已完成') else None,
            completed_at=now - timedelta(minutes=10) if status == '已完成' else None,
            escalated=escalated,
            created_at=created,
        )

    # 1. 水电工单，提交 10 分钟，30 分钟时限：待响应、未超时
    t1 = make_ticket(fault_type='水电', minutes_ago=10, description='厨房插座没电')
    # 2. 门锁工单，提交 45 分钟：已超时、未升级
    t2 = make_ticket(fault_type='门锁', minutes_ago=45, description='入户门反锁打不开')
    # 3. 管道工单，提交 5 小时（4 小时时限）：已超时、未升级
    t3 = make_ticket(fault_type='管道', minutes_ago=300, description='卫生间下水管道堵塞')
    # 4. 家电工单，提交 1 小时：待响应、未超时
    t4 = make_ticket(fault_type='家电', minutes_ago=60, description='空调不制冷')
    # 5. 已被王建国接单，处理中
    t5 = make_ticket(fault_type='水电', minutes_ago=50, status='处理中', assignee=staff[0],
                     description='客厅灯闪烁')
    # 6. 已超时并升级过一次，已转派给李秀兰（仍待响应）
    t6 = make_ticket(fault_type='门锁', minutes_ago=90, assignee=staff[1], escalated=True,
                     description='阳台推拉门锁损坏')
    # 7. 已完成工单
    t7 = make_ticket(fault_type='其他', minutes_ago=200, status='已完成', assignee=staff[2],
                     description='楼道照明损坏')

    def submit_event(ticket, created):
        TicketEvent.objects.create(ticket=ticket, event_type='提交', remark='住户提交', created_at=created)

    submit_event(t1, t1.created_at)
    submit_event(t2, t2.created_at)
    submit_event(t3, t3.created_at)
    submit_event(t4, t4.created_at)
    submit_event(t5, t5.created_at)
    submit_event(t6, t6.created_at)
    submit_event(t7, t7.created_at)

    TicketEvent.objects.create(
        ticket=t5, event_type='接单', operator=staff[0],
        remark='王建国 接单', created_at=now - timedelta(minutes=45),
    )
    TicketEvent.objects.create(
        ticket=t6, event_type='升级', operator=staff[1], to_assignee=staff[1],
        remark='超时未接单，升级转派给 李秀兰', created_at=now - timedelta(minutes=55),
    )
    TicketEvent.objects.create(
        ticket=t7, event_type='接单', operator=staff[2],
        remark='张师傅 接单', created_at=now - timedelta(minutes=180),
    )
    TicketEvent.objects.create(
        ticket=t7, event_type='完成', operator=staff[2],
        remark='张师傅 完成维修', created_at=now - timedelta(minutes=10),
    )


def remove_demo_data(apps, schema_editor):
    RepairStaff = apps.get_model('repair', 'RepairStaff')
    RepairStaff.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('repair', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, remove_demo_data),
    ]
