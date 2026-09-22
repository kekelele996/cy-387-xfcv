from django.core.management.base import BaseCommand

from app.apps.repair.services import escalate_overdue_batch
from app.utils.logger import get_logger

logger = get_logger('repair')


class Command(BaseCommand):
    help = '将所有超过分级响应时限仍未接单的工单升级一次，转派给未完成工单最少的物业人员。'

    def handle(self, *args, **options):
        escalated = escalate_overdue_batch()
        for ticket in escalated:
            logger.info('escalated ticket %s -> %s', ticket.id, ticket.assignee.name)
        self.stdout.write(f'已升级 {len(escalated)} 张超时工单')
