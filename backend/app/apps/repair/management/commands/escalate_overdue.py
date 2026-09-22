"""扫描超时未接单工单并升级。可由 cron/celery beat 周期调用。"""
from django.core.management.base import BaseCommand

from app.apps.repair.services import escalate_overdue_tickets
from app.utils.logger import get_logger

logger = get_logger('repair')


class Command(BaseCommand):
    help = '扫描所有超过响应时限且未接单的报修工单，各升级一次'

    def handle(self, *args, **options):
        tickets = escalate_overdue_tickets()
        for ticket in tickets:
            logger.info('ticket #%s escalated to staff #%s', ticket.id, ticket.assignee_id)
        self.stdout.write(f'升级完成，共 {len(tickets)} 个工单')
