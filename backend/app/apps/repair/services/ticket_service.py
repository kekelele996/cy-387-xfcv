"""报修工单的提交、接单、完成操作：每次状态变更与事件流水在同一事务内提交。"""
from django.db import transaction
from django.utils import timezone

from app.constants.errors import ERROR_CODES
from app.utils.db_retry import retry_on_db_lock
from app.utils.errors import BusinessError
from app.utils.logger import get_logger
from ..models import RepairStaff, RepairTicket, TicketEvent
from .sla import calc_response_deadline

logger = get_logger('repair')


def _get_staff(staff_id) -> RepairStaff:
    try:
        return RepairStaff.objects.get(pk=staff_id, is_active=True)
    except (RepairStaff.DoesNotExist, ValueError, TypeError):
        raise BusinessError(ERROR_CODES['REPAIR_STAFF_NOT_FOUND'], status_code=404)


@retry_on_db_lock()
def create_ticket(*, fault_type: str, description: str, submitter_name: str = '', photo=None) -> RepairTicket:
    """住户提交报修工单，按故障类型写入响应截止时间。"""
    if not description or not str(description).strip():
        raise BusinessError(ERROR_CODES['REPAIR_INVALID'], status_code=400)

    submitted_at = timezone.now()
    with transaction.atomic():
        ticket = RepairTicket(
            fault_type=fault_type,
            description=str(description).strip(),
            submitter_name=submitter_name,
            photo=photo or None,
            response_deadline=submitted_at,
        )
        ticket.save()
        # created_at 落库后再以其为基准计算分级响应截止时间，保证时限精确
        ticket.response_deadline = calc_response_deadline(fault_type, ticket.created_at)
        ticket.save(update_fields=['response_deadline'])
        TicketEvent.objects.create(ticket=ticket, event_type='提交', remark=submitter_name)
    logger.info('repair ticket #%s submitted (%s), deadline=%s', ticket.id, fault_type, ticket.response_deadline)
    return ticket


@retry_on_db_lock()
def accept_ticket(ticket_id: int, staff_id: int) -> RepairTicket:
    """物业人员接单：记录处理人和接单时间。并发接单只有一方成功。"""
    with transaction.atomic():
        try:
            ticket = RepairTicket.objects.select_for_update().get(pk=ticket_id)
        except RepairTicket.DoesNotExist:
            raise BusinessError(ERROR_CODES['REPAIR_TICKET_NOT_FOUND'], status_code=404)
        staff = _get_staff(staff_id)

        if ticket.status != '待响应':
            raise BusinessError(ERROR_CODES['REPAIR_ALREADY_RESPONDED'], status_code=409)
        if ticket.assignee_id and ticket.assignee_id != staff.id:
            raise BusinessError(ERROR_CODES['REPAIR_ALREADY_RESPONDED'], status_code=409)

        ticket.assignee = staff
        ticket.accepted_at = timezone.now()
        ticket.status = '处理中'
        ticket.save(update_fields=['assignee', 'accepted_at', 'status', 'updated_at'])
        TicketEvent.objects.create(
            ticket=ticket, event_type='接单', operator=staff,
            remark=f'{staff.name} 接单',
        )
    logger.info('repair ticket #%s accepted by staff #%s', ticket_id, staff_id)
    return ticket


@retry_on_db_lock()
def complete_ticket(ticket_id: int, staff_id: int) -> RepairTicket:
    """处理中工单由当前处理人标记完成。"""
    with transaction.atomic():
        try:
            ticket = RepairTicket.objects.select_for_update().get(pk=ticket_id)
        except RepairTicket.DoesNotExist:
            raise BusinessError(ERROR_CODES['REPAIR_TICKET_NOT_FOUND'], status_code=404)
        staff = _get_staff(staff_id)

        if ticket.status == '已完成':
            raise BusinessError(ERROR_CODES['REPAIR_ALREADY_COMPLETED'], status_code=409)
        if ticket.status != '处理中' or ticket.assignee_id != staff.id:
            raise BusinessError(ERROR_CODES['REPAIR_NOT_ACCEPTED'], status_code=409)

        ticket.status = '已完成'
        ticket.completed_at = timezone.now()
        ticket.save(update_fields=['status', 'completed_at', 'updated_at'])
        TicketEvent.objects.create(
            ticket=ticket, event_type='完成', operator=staff,
            remark=f'{staff.name} 完成维修',
        )
    logger.info('repair ticket #%s completed by staff #%s', ticket_id, staff_id)
    return ticket
