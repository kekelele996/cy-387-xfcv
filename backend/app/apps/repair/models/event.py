from django.db import models

from app.constants.enums import REPAIR_EVENT_TYPES
from .staff import RepairStaff
from .ticket import RepairTicket


class TicketEvent(models.Model):
    """工单事件流水：提交、接单、升级、完成均留痕，升级记录不可被覆盖。"""

    EVENT_TYPE_CHOICES = [(value, value) for value in REPAIR_EVENT_TYPES]

    ticket = models.ForeignKey(RepairTicket, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField('事件类型', max_length=10, choices=EVENT_TYPE_CHOICES)
    operator = models.ForeignKey(
        RepairStaff, verbose_name='操作物业人员', on_delete=models.PROTECT,
        related_name='events', null=True, blank=True,
    )
    from_assignee = models.ForeignKey(
        RepairStaff, on_delete=models.PROTECT, related_name='transfer_out_events',
        null=True, blank=True,
    )
    to_assignee = models.ForeignKey(
        RepairStaff, on_delete=models.PROTECT, related_name='transfer_in_events',
        null=True, blank=True,
    )
    remark = models.CharField('备注', max_length=255, blank=True, default='')
    created_at = models.DateTimeField('发生时间', auto_now_add=True)

    class Meta:
        db_table = 'repair_ticket_event'
        ordering = ['id']
        verbose_name = '工单事件'
        verbose_name_plural = verbose_name
