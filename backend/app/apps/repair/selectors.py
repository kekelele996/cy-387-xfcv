"""报修工单查询：筛选条件与超时判定统一在这里维护，保证页面刷新后一致。"""
from django.db.models.expressions import Exists, OuterRef
from django.utils import timezone

from .models import RepairStaff, TicketEvent, RepairTicket

VALID_FILTERS = {'all', 'pending', 'overdue', 'processing', 'completed'}


def get_ticket_queryset(filter_status: str = 'all'):
    """支持按待响应、已超时、处理中、已完成筛选。

    已超时 = 状态待响应且当前时间已超过响应截止时间，以数据库 now() 为准，
    这样所有客户端刷新页面看到的结果一致。
    """
    queryset = (
        RepairTicket.objects.select_related('assignee')
        .prefetch_related('events__operator', 'events__from_assignee', 'events__to_assignee')
        .annotate(
            is_overdue_annotation=Exists(
                RepairTicket.objects.filter(
                    pk=OuterRef('pk'),
                    status='待响应',
                    response_deadline__lt=timezone.now(),
                )
            )
        )
    )
    if filter_status == 'pending':
        queryset = queryset.filter(status='待响应')
    elif filter_status == 'overdue':
        queryset = queryset.filter(status='待响应', response_deadline__lt=timezone.now())
    elif filter_status == 'processing':
        queryset = queryset.filter(status='处理中')
    elif filter_status == 'completed':
        queryset = queryset.filter(status='已完成')
    return queryset


def list_active_staff():
    return RepairStaff.objects.filter(is_active=True).order_by('id')


def list_ticket_events(ticket_id: int):
    return TicketEvent.objects.filter(ticket_id=ticket_id).select_related(
        'operator', 'from_assignee', 'to_assignee'
    ).order_by('id')
