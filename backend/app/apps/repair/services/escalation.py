"""超时升级：只能升级一次，转派给未完成工单最少的在岗物业人员。

并发安全与原子性：
- 对工单加行锁（select_for_update），并发升级请求串行化；
- escalated 作为幂等标记，重复升级直接报错，不会重复转派；
- 转派人员、升级标记、升级事件流水在同一个事务内提交，成功则全部生效，失败则全部不变。
"""
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from app.constants.errors import ERROR_CODES
from app.utils.db_retry import retry_on_db_lock
from app.utils.errors import BusinessError
from app.utils.logger import get_logger
from ..models import RepairStaff, RepairTicket, TicketEvent

logger = get_logger('repair')

UNFINISHED_STATES = ('待响应', '处理中')


def pick_least_loaded_staff(exclude_id=None) -> RepairStaff:
    """选择未完成（待响应/处理中）工单数最少的在岗物业人员，同数取入职最早者。"""
    staff = (
        RepairStaff.objects.filter(is_active=True)
        .exclude(pk=exclude_id)
        .annotate(open_count=Count('tickets', filter=Q(tickets__status__in=UNFINISHED_STATES)))
        .order_by('open_count', 'id')
    )
    staff_locked = [item for item in staff.select_for_update()]
    if not staff_locked:
        raise BusinessError(ERROR_CODES['REPAIR_NO_STAFF_AVAILABLE'], status_code=409)
    return staff_locked[0]


@retry_on_db_lock()
def escalate_ticket(ticket_id: int) -> RepairTicket:
    """升级单个超时未接单工单。任何校验失败都会整体回滚。"""
    with transaction.atomic():
        try:
            ticket = RepairTicket.objects.select_for_update().select_related('assignee').get(pk=ticket_id)
        except RepairTicket.DoesNotExist:
            raise BusinessError(ERROR_CODES['REPAIR_TICKET_NOT_FOUND'], status_code=404)

        if ticket.status != '待响应':
            raise BusinessError(ERROR_CODES['REPAIR_TICKET_NOT_PENDING'], status_code=409)
        if ticket.escalated:
            # 重复或并发升级：已升级过，拒绝并保证不会重复转派
            raise BusinessError(ERROR_CODES['REPAIR_ALREADY_ESCALATED'], status_code=409)
        if timezone.now() <= ticket.response_deadline:
            raise BusinessError(ERROR_CODES['REPAIR_NOT_OVERDUE'], status_code=409)

        previous = ticket.assignee
        target = pick_least_loaded_staff(exclude_id=previous.id if previous else None)

        ticket.assignee = target
        ticket.escalated = True
        ticket.save(update_fields=['assignee', 'escalated', 'updated_at'])
        TicketEvent.objects.create(
            ticket=ticket,
            event_type='升级',
            operator=target,
            from_assignee=previous,
            to_assignee=target,
            remark=f'超时未接单，升级转派给 {target.name}',
        )
    logger.info('repair ticket #%s escalated to staff #%s', ticket_id, target.id)
    return ticket


def escalate_overdue_tickets() -> list[RepairTicket]:
    """扫描所有已超时、未接单且未升级过的工单，逐个执行单次升级。

    每个工单独立事务，单个失败不影响其他工单；已被其他请求升级的工单会被跳过，
    因此并发触发扫描也不会重复转派。
    """
    now = timezone.now()
    overdue_ids = list(
        RepairTicket.objects.filter(
            status='待响应', escalated=False, response_deadline__lt=now,
        ).values_list('id', flat=True)
    )
    escalated = []
    for ticket_id in overdue_ids:
        try:
            escalated.append(escalate_ticket(ticket_id))
        except BusinessError:
            logger.info('skip ticket #%s during overdue scan', ticket_id)
    return escalated
