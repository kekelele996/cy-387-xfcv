from django.db import models


class RepairStaff(models.Model):
    """物业维修人员：超时升级时按未完成工单数选择转派对象。"""

    name = models.CharField('姓名', max_length=40, unique=True)
    phone = models.CharField('联系电话', max_length=30, blank=True, default='')
    is_active = models.BooleanField('在岗', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'repair_staff'
        verbose_name = '物业维修人员'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
