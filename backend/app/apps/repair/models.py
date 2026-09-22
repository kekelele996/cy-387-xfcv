from django.db import models
from app.constants import enums


class RepairStaff(models.Model):
    """物业维修人员。"""

    name = models.CharField(max_length=40, unique=True)
    phone = models.CharField(max_length=30, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'repair_staff'
        verbose_name = '物业人员'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class RepairTicket(models.Model):
    """物业报修工单。"""

    fault_type = models.CharField(max_length=20, choices=[(t, t) for t in enums.REPAIR_TYPES])
    description = models.TextField()
    photo = models.ImageField(upload_to='repairs/', blank=True, null=True)
    resident_name = models.CharField(max_length=40, blank=True, default='')
    resident_phone = models.CharField(max_length=30, blank=True, default='')

    status = models.CharField(
        max_length=20,
        choices=[(s, s) for s in enums.REPAIR_STATUS],
        default=enums.REPAIR_STATUS_PENDING,
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    response_deadline = models.DateTimeField()

    assignee = models.ForeignKey(
        RepairStaff,
        on_delete=models.PROTECT,
        related_name='tickets',
        null=True,
        blank=True,
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    previous_assignee = models.ForeignKey(
        RepairStaff,
        on_delete=models.PROTECT,
        related_name='escalated_from_tickets',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'repair_ticket'
        verbose_name = '报修工单'
        verbose_name_plural = verbose_name
        ordering = ['-submitted_at']

    def __str__(self):
        return f'#{self.pk} {self.fault_type} {self.status}'


class RepairEvent(models.Model):
    """工单流转记录：提交、接单、升级、完成。"""

    ticket = models.ForeignKey(RepairTicket, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=[(t, t) for t in enums.REPAIR_EVENT_TYPES])
    operator = models.ForeignKey(
        RepairStaff,
        on_delete=models.PROTECT,
        related_name='handled_events',
        null=True,
        blank=True,
    )
    detail = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'repair_event'
        verbose_name = '工单流转记录'
        verbose_name_plural = verbose_name
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.ticket_id}-{self.event_type}'
