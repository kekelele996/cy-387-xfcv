"""物业人员对工单执行的动作：接单、完成。"""
from rest_framework.response import Response
from rest_framework.views import APIView

from ..selectors import get_ticket_queryset
from ..serializers import RepairTicketSerializer
from ..services import accept_ticket, complete_ticket


class TicketAcceptView(APIView):
    def post(self, request, ticket_id: int):
        """接单：记录处理人和接单时间。"""
        staff_id = request.data.get('staffId')
        ticket = accept_ticket(ticket_id, staff_id)
        ticket = get_ticket_queryset().get(pk=ticket.pk)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)


class TicketCompleteView(APIView):
    def post(self, request, ticket_id: int):
        """完成：仅当前处理人可操作。"""
        staff_id = request.data.get('staffId')
        ticket = complete_ticket(ticket_id, staff_id)
        ticket = get_ticket_queryset().get(pk=ticket.pk)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)
