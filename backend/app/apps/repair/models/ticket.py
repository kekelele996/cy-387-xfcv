from django.db import models

from app.constants.enums import REPAIR_TICKET_STATUS, REPAIR_TYPES
from .staff import RepairStaff


class RepairTicket(models.Model):
    """报修工单：含分级响应截止时间、接单留痕和单次升级标记。"""

    FAULT_TYPE_CHOICES = [(value, value) for value in REPAIR_TYPES]
    STATUS_CHOICES = [(value, value) for value in REPAIR_TICKET_STATUS]

    fault_type = models.CharField('故障类型', max_length=10, choices=FAULT_TYPE_CHOICES)
    description = models.CharField('故障描述', max_length=500)
    photo = models.ImageField('故障照片', upload_to='repair/', blank=True, null=True)
    submitter_name = models.CharField('报修住户', max_length=40, blank=True, default='')

    status = models.CharField('工单状态', max_length=10, choices=STATUS_CHOICES, default='待响应', db_index=True)
    assignee = models.ForeignKey(
        RepairStaff, verbose_name='当前处理人', on_delete=models.PROTECT,
        related_name='tickets', null=True, blank=True,
    )

    response_deadline = models.DateTimeField('响应截止时间', db_index=True)
    accepted_at = models.DateTimeField('接单时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    escalated = models.BooleanField('是否已升级', default=False)
    created_at = models.DateTimeField('提交时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'repair_ticket'
        ordering = ['-created_at']
        verbose_name = '报修工单'
        verbose_name_plural = verbose_name

    @property
    def is_overdue(self) -> bool:
        """超过响应截止时间且仍处于待响应状态即为已超时。"""
        from django.utils import timezone
        return self.status == '待响应' and timezone.now() > self.response_deadline

    def __str__(self):
        return f'#{self.pk} {self.fault_type}'
