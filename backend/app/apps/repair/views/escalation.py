"""超时升级：单个升级 + 批量扫描超时未接单工单。"""
from rest_framework.response import Response
from rest_framework.views import APIView

from ..selectors import get_ticket_queryset
from ..serializers import RepairTicketSerializer
from ..services import escalate_overdue_tickets, escalate_ticket


class TicketEscalateView(APIView):
    def post(self, request, ticket_id: int):
        """超时未接单工单升级一次，转派给未完成工单最少的物业人员。"""
        ticket = escalate_ticket(ticket_id)
        ticket = get_ticket_queryset().get(pk=ticket.pk)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)


class TicketEscalateScanView(APIView):
    def post(self, request):
        """扫描并升级全部已超时工单；重复/并发调用不会重复转派。"""
        tickets = escalate_overdue_tickets()
        data = RepairTicketSerializer(
            [get_ticket_queryset().get(pk=item.pk) for item in tickets],
            many=True,
            context={'request': request},
        ).data
        return Response({'escalatedCount': len(data), 'tickets': data})
