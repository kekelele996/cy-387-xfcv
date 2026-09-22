import functools
import logging
import time
from datetime import timedelta

from django.conf import settings
from django.db import OperationalError, transaction
from django.db.models import Count, Q
from django.utils import timezone

from app.constants.enums import (
    REPAIR_EVENT_ACCEPT,
    REPAIR_EVENT_COMPLETE,
    REPAIR_EVENT_ESCALATE,
    REPAIR_EVENT_SUBMIT,
    REPAIR_STATUS_COMPLETED,
    REPAIR_STATUS_PENDING,
    REPAIR_STATUS_PROCESSING,
    RESPONSE_DEADLINE_MINUTES,
)
from .exceptions import RepairError
from .models import RepairEvent, RepairStaff, RepairTicket

logger = logging.getLogger('rentfind.repair')

# 未完成工单状态：待响应与处理中均计入物业人员在手工单量。
UNFINISHED_STATUSES = (REPAIR_STATUS_PENDING, REPAIR_STATUS_PROCESSING)


def _retry_on_sqlite_lock(func):
    """SQLite 锁升级可能立即返回 database is locked（不经过 busy_timeout 等待）。

    生产数据库为 PostgreSQL，依靠行锁阻塞等待，不会发生该错误；
    仅在本地 SQLite 下对写事务做短暂退避重试，使其语义与行锁等待一致。
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        is_sqlite = 'sqlite' in settings.DATABASES['default']['ENGINE']
        last_error = None
        for attempt in range(8 if is_sqlite else 1):
            try:
                return func(*args, **kwargs)
            except OperationalError as exc:
                last_error = exc
                if not is_sqlite or 'locked' not in str(exc).lower():
                    raise
                time.sleep(0.05 * (attempt + 1))
        raise last_error

    return wrapper


def is_overdue(ticket, now=None):
    """超过分级响应时限仍未接单即为超时。"""
    now = now or timezone.now()
    return ticket.accepted_at is None and now > ticket.response_deadline


def create_ticket(data):
    """住户提交报修工单，按故障类型计算响应截止时间。"""
    deadline_minutes = RESPONSE_DEADLINE_MINUTES[data['fault_type']]
    submitted_at = timezone.now()
    ticket = RepairTicket.objects.create(
        fault_type=data['fault_type'],
        description=data['description'],
        photo=data.get('photo'),
        resident_name=data.get('resident_name', ''),
        resident_phone=data.get('resident_phone', ''),
        response_deadline=submitted_at + timedelta(minutes=deadline_minutes),
    )
    RepairEvent.objects.create(
        ticket=ticket,
        event_type=REPAIR_EVENT_SUBMIT,
        detail=f'住户提交{ticket.fault_type}报修，要求{deadline_minutes}分钟内响应',
    )
    logger.info('repair ticket created id=%s type=%s deadline=%s', ticket.id, ticket.fault_type, ticket.response_deadline)
    return ticket


def _pick_target_staff(current_assignee_id):
    """选择未完成工单最少的物业人员；并列时取入职最早者，保证结果唯一可预期。"""
    staff_list = list(RepairStaff.objects.order_by('id'))
    candidates = [staff for staff in staff_list if staff.id != current_assignee_id]
    if not candidates:
        raise RepairError('REPAIR_NO_AVAILABLE_STAFF', 409)

    counts = {
        row['assignee_id']: row['n']
        for row in (
            RepairTicket.objects.filter(assignee__in=candidates, status__in=UNFINISHED_STATUSES)
            .values('assignee_id')
            .annotate(n=Count('id'))
        )
    }
    return min(candidates, key=lambda staff: (counts.get(staff.id, 0), staff.id))


@_retry_on_sqlite_lock
@transaction.atomic
def accept_ticket(ticket_id, staff_id):
    """物业人员接单，记录处理人与接单时间。

    写事务内以条件更新充当并发闸门（WHERE 未接单）：
    只有一个并发事务能更新成功，其余整体回滚，状态、处理人、记录保持不变。
    """
    staff = _get_staff(staff_id)
    ticket = _get_ticket(ticket_id)

    accepted_at = timezone.now()
    # 互斥闸门（与 escalate_ticket 对称）：
    # - status='待响应'：一旦有接单成功，状态变处理中，升级条件不再成立；
    # - accepted_at IS NULL：重复/并发接单只有一笔成功；
    # - 未升级，或已升级且已指派给本人：升级先发生时只有被指派师傅可以接单，
    #   从而“接单”与“升级”的并发组合不可能同时成功（SQLite 旧快照下同样成立，
    #   因为 UPDATE 的 WHERE 按语句执行时的最新数据判定）。
    updated = RepairTicket.objects.filter(
        pk=ticket.pk,
        status=REPAIR_STATUS_PENDING,
        accepted_at__isnull=True,
    ).filter(
        # escalated=False OR assignee_id=staff.id
        Q(escalated=False) | Q(assignee_id=staff.id)
    ).update(
        assignee=staff,
        accepted_at=accepted_at,
        status=REPAIR_STATUS_PROCESSING,
    )
    if not updated:
        # 并发竞争落败：重读最新状态，返回准确的业务错误，本事务整体回滚。
        latest = RepairTicket.objects.filter(pk=ticket.pk).values_list(
            'status', 'accepted_at', 'escalated', 'assignee_id'
        ).first()
        if latest is None:
            raise RepairError('REPAIR_TICKET_NOT_FOUND', 404)
        status, accepted, escalated, assignee_id = latest
        if status == REPAIR_STATUS_COMPLETED:
            raise RepairError('REPAIR_ALREADY_COMPLETED', 409)
        if accepted is not None:
            raise RepairError('REPAIR_ALREADY_ACCEPTED', 409)
        if escalated and assignee_id != staff.id:
            raise RepairError('REPAIR_STAFF_NOT_ASSIGNED', 409)
        raise RepairError('REPAIR_ALREADY_ACCEPTED', 409)

    RepairEvent.objects.create(
        ticket=ticket,
        event_type=REPAIR_EVENT_ACCEPT,
        operator=staff,
        detail=f'{staff.name} 接单处理',
    )
    logger.info('repair ticket accepted id=%s staff=%s at=%s', ticket.id, staff.name, accepted_at)
    return RepairTicket.objects.select_related('assignee').get(pk=ticket.pk)


@_retry_on_sqlite_lock
@transaction.atomic
def escalate_ticket(ticket_id):
    """超时工单升级：仅可升级一次，转派给未完成工单最少的物业人员。

    状态、处理人、升级标记与升级记录在同一个事务中提交，要么一并成功，要么全部不变。
    并发安全性由条件更新（WHERE escalated = FALSE AND 未接单）保证：
    竞争事务在写锁处串行，先到者更新 1 行，后来者更新 0 行并整体回滚，
    因而重复或并发升级都不会产生第二次转派。PostgreSQL 下写锁为行级锁。
    """
    ticket = _get_ticket(ticket_id)

    if ticket.status == REPAIR_STATUS_COMPLETED:
        raise RepairError('REPAIR_ALREADY_COMPLETED', 409)
    if ticket.accepted_at is not None:
        raise RepairError('REPAIR_ALREADY_ACCEPTED', 409)
    if ticket.escalated:
        raise RepairError('REPAIR_ALREADY_ESCALATED', 409)
    if timezone.now() <= ticket.response_deadline:
        raise RepairError('REPAIR_NOT_OVERDUE', 400)

    target = _pick_target_staff(ticket.assignee_id)
    previous = ticket.assignee
    now = timezone.now()

    updated = RepairTicket.objects.filter(
        pk=ticket.pk,
        escalated=False,
        accepted_at__isnull=True,
        status=REPAIR_STATUS_PENDING,
    ).update(
        previous_assignee_id=ticket.assignee_id,
        assignee=target,
        escalated=True,
        escalated_at=now,
    )
    if not updated:
        latest = RepairTicket.objects.filter(pk=ticket.pk).values_list(
            'status', 'accepted_at', 'escalated'
        ).first()
        if latest is None:
            raise RepairError('REPAIR_TICKET_NOT_FOUND', 404)
        status, accepted, escalated = latest
        if status == REPAIR_STATUS_COMPLETED:
            raise RepairError('REPAIR_ALREADY_COMPLETED', 409)
        if accepted is not None:
            raise RepairError('REPAIR_ALREADY_ACCEPTED', 409)
        raise RepairError('REPAIR_ALREADY_ESCALATED', 409)

    from_text = previous.name if previous is not None else '待派单池'
    RepairEvent.objects.create(
        ticket=ticket,
        event_type=REPAIR_EVENT_ESCALATE,
        detail=f'超过响应时限未接单，由{from_text}升级转派给 {target.name}（在手未完成工单最少）',
    )
    logger.warning('repair ticket escalated id=%s from=%s to=%s', ticket.id, from_text, target.name)
    return RepairTicket.objects.select_related('assignee', 'previous_assignee').get(pk=ticket.pk)


@_retry_on_sqlite_lock
@transaction.atomic
def complete_ticket(ticket_id):
    """工单处理完成。"""
    ticket = _get_ticket(ticket_id)
    if ticket.accepted_at is None:
        raise RepairError('REPAIR_ALREADY_ACCEPTED', 400)

    completed_at = timezone.now()
    updated = (
        RepairTicket.objects.filter(pk=ticket.pk, accepted_at__isnull=False)
        .exclude(status=REPAIR_STATUS_COMPLETED)
        .update(status=REPAIR_STATUS_COMPLETED, completed_at=completed_at)
    )
    if not updated:
        raise RepairError('REPAIR_ALREADY_COMPLETED', 409)

    RepairEvent.objects.create(
        ticket=ticket,
        event_type=REPAIR_EVENT_COMPLETE,
        operator=ticket.assignee,
        detail=f'{ticket.assignee.name} 完成处理',
    )
    logger.info('repair ticket completed id=%s staff=%s', ticket.id, ticket.assignee.name)
    return RepairTicket.objects.select_related('assignee').get(pk=ticket.pk)


def escalate_overdue_batch():
    """批量升级所有超时未接单工单（供定时任务调用，逐单事务，天然幂等）。"""
    overdue_ids = RepairTicket.objects.filter(
        status=REPAIR_STATUS_PENDING,
        accepted_at__isnull=True,
        escalated=False,
        response_deadline__lt=timezone.now(),
    ).values_list('id', flat=True)
    escalated = []
    for ticket_id in overdue_ids:
        try:
            escalated.append(escalate_ticket(ticket_id))
        except RepairError:
            # 并发场景下可能已被其他进程升级，跳过即可。
            continue
    return escalated


def _get_ticket(ticket_id):
    try:
        return RepairTicket.objects.select_related('assignee', 'previous_assignee').get(pk=ticket_id)
    except RepairTicket.DoesNotExist:
        raise RepairError('REPAIR_TICKET_NOT_FOUND', 404)


def _get_staff(staff_id):
    try:
        return RepairStaff.objects.get(pk=staff_id)
    except RepairStaff.DoesNotExist:
        raise RepairError('REPAIR_STAFF_NOT_FOUND', 404)
