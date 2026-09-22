"""报修工单：提交、列表筛选、详情。"""
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from app.constants.errors import ERROR_CODES
from app.utils.errors import BusinessError
from ..models import RepairTicket
from ..selectors import VALID_FILTERS, get_ticket_queryset
from ..serializers import RepairTicketCreateSerializer, RepairTicketSerializer
from ..services import create_ticket


class TicketListCreateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        """按状态筛选工单：待响应、已超时等；结果与计时均以服务端时间为准。"""
        filter_status = request.query_params.get('status', 'all')
        if filter_status not in VALID_FILTERS:
            raise BusinessError(ERROR_CODES['REPAIR_INVALID'], status_code=400)
        tickets = get_ticket_queryset(filter_status)
        return Response(RepairTicketSerializer(tickets, many=True, context={'request': request}).data)

    def post(self, request):
        """住户提交报修，按故障类型自动计算响应截止时间。"""
        payload = RepairTicketCreateSerializer(data=request.data)
        if not payload.is_valid():
            raise BusinessError(ERROR_CODES['REPAIR_INVALID'], status_code=400)
        data = payload.validated_data
        ticket = create_ticket(
            fault_type=data['faultType'],
            description=data['description'],
            submitter_name=data.get('submitterName', ''),
            photo=data.get('photo'),
        )
        ticket = get_ticket_queryset().get(pk=ticket.pk)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data, status=201)


class TicketDetailView(APIView):
    def get(self, request, ticket_id: int):
        try:
            ticket = get_ticket_queryset().get(pk=ticket_id)
        except RepairTicket.DoesNotExist:
            raise BusinessError(ERROR_CODES['REPAIR_TICKET_NOT_FOUND'], status_code=404)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)
