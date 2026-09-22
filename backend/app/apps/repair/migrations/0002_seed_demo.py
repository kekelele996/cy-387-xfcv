from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def seed_demo(apps, schema_editor):
    RepairStaff = apps.get_model('repair', 'RepairStaff')
    RepairTicket = apps.get_model('repair', 'RepairTicket')
    RepairEvent = apps.get_model('repair', 'RepairEvent')

    if RepairTicket.objects.exists():
        return

    wang, _ = RepairStaff.objects.get_or_create(name='王师傅', defaults={'phone': '13800000101'})
    li, _ = RepairStaff.objects.get_or_create(name='李师傅', defaults={'phone': '13800000102'})
    zhao, _ = RepairStaff.objects.get_or_create(name='赵师傅', defaults={'phone': '13800000103'})

    now = timezone.now()

    def add_ticket(fault_type, minutes_ago, deadline_minutes, description, **kwargs):
        submitted_at = now - timedelta(minutes=minutes_ago)
        ticket = RepairTicket.objects.create(
            fault_type=fault_type,
            description=description,
            resident_name=kwargs.get('resident_name', '住户'),
            resident_phone=kwargs.get('resident_phone', '13900000000'),
            status=kwargs.get('status', '待响应'),
            submitted_at=submitted_at,
            response_deadline=submitted_at + timedelta(minutes=deadline_minutes),
            assignee=kwargs.get('assignee'),
            accepted_at=kwargs.get('accepted_at'),
            escalated=kwargs.get('escalated', False),
            escalated_at=kwargs.get('escalated_at'),
            previous_assignee=kwargs.get('previous_assignee'),
            completed_at=kwargs.get('completed_at'),
        )
        RepairEvent.objects.create(
            ticket=ticket,
            event_type='提交',
            detail=f'住户提交{fault_type}报修，要求{deadline_minutes}分钟内响应',
            created_at=submitted_at,
        )
        return ticket

    # 1. 水电：10 分钟前提交，30 分钟时限，待响应（计时中）。
    add_ticket('水电', 10, 30, '厨房水龙头不出水，疑似停水。')

    # 2. 门锁：40 分钟前提交仍未接单，已超时、未升级（可触发升级）。
    add_ticket('门锁', 40, 30, '入户门锁打不开，被锁在门外。')

    # 3. 管道：5 小时前提交，已超时并升级给王师傅，仍未接单。
    t3 = add_ticket(
        '管道', 300, 240, '卫生间地漏反水，地面有积水。',
        assignee=wang,
        escalated=True,
        escalated_at=now - timedelta(minutes=30),
        previous_assignee=None,
    )
    RepairEvent.objects.create(
        ticket=t3,
        event_type='升级',
        detail='超过响应时限未接单，由待派单池升级转派给 王师傅（在手未完成工单最少）',
        created_at=now - timedelta(minutes=30),
    )

    # 4. 家电：2 小时前提交，李师傅在时限内接单，处理中。
    t4 = add_ticket(
        '家电', 120, 240, '空调不制冷，外机有异响。',
        status='处理中',
        assignee=li,
        accepted_at=now - timedelta(minutes=90),
    )
    RepairEvent.objects.create(
        ticket=t4,
        event_type='接单',
        operator=li,
        detail='李师傅 接单处理',
        created_at=now - timedelta(minutes=90),
    )

    # 5. 其他：昨天提交，赵师傅已接单并完成。
    t5 = add_ticket(
        '其他', 60 * 26, 240, '楼道感应灯损坏。',
        status='已完成',
        assignee=zhao,
        accepted_at=now - timedelta(hours=25),
        completed_at=now - timedelta(hours=24),
        resident_name='刘女士',
    )
    RepairEvent.objects.create(
        ticket=t5,
        event_type='接单',
        operator=zhao,
        detail='赵师傅 接单处理',
        created_at=now - timedelta(hours=25),
    )
    RepairEvent.objects.create(
        ticket=t5,
        event_type='完成',
        operator=zhao,
        detail='赵师傅 完成处理',
        created_at=now - timedelta(hours=24),
    )


def remove_demo(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('repair', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_demo, remove_demo),
    ]
