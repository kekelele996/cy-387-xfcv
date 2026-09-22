from django.db.models import Count, Q
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from app.constants.enums import (
    REPAIR_STATUS_COMPLETED,
    REPAIR_STATUS_PENDING,
    REPAIR_STATUS_PROCESSING,
)
from . import services
from .models import RepairStaff, RepairTicket
from .serializers import RepairStaffSerializer, RepairTicketSerializer


class RepairTicketListCreateView(APIView):
    """工单提交与列表。列表支持按「待响应 / 已超时」等条件筛选。"""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        queryset = RepairTicket.objects.select_related(
            'assignee', 'previous_assignee'
        ).prefetch_related('events', 'events__operator')

        status = request.query_params.get('status')
        if status in (REPAIR_STATUS_PENDING, REPAIR_STATUS_PROCESSING, REPAIR_STATUS_COMPLETED):
            queryset = queryset.filter(status=status)

        overdue = request.query_params.get('overdue')
        if overdue in ('true', 'false'):
            from django.utils import timezone
            overdue_q = Q(accepted_at__isnull=True) & Q(response_deadline__lt=timezone.now())
            queryset = queryset.filter(overdue_q if overdue == 'true' else ~overdue_q)

        fault_type = request.query_params.get('faultType')
        if fault_type:
            queryset = queryset.filter(fault_type=fault_type)

        serializer = RepairTicketSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = RepairTicketSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        ticket = services.create_ticket(serializer.validated_data)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data, status=201)


class RepairTicketDetailView(APIView):
    def get(self, request, ticket_id):
        ticket = self._get_ticket(ticket_id)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)

    def _get_ticket(self, ticket_id):
        from .exceptions import RepairError
        try:
            return RepairTicket.objects.select_related('assignee', 'previous_assignee').prefetch_related(
                'events', 'events__operator'
            ).get(pk=ticket_id)
        except RepairTicket.DoesNotExist:
            raise RepairError('REPAIR_TICKET_NOT_FOUND', 404)


class RepairAcceptView(APIView):
    """物业接单：记录处理人与接单时间。"""

    def post(self, request, ticket_id):
        staff_id = request.data.get('staffId')
        if not staff_id:
            from .exceptions import RepairError
            raise RepairError('REPAIR_STAFF_NOT_FOUND', 400)
        ticket = services.accept_ticket(ticket_id, staff_id)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)


class RepairEscalateView(APIView):
    """超时工单升级：仅一次，转派给未完成工单最少的物业人员。"""

    def post(self, request, ticket_id):
        ticket = services.escalate_ticket(ticket_id)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)


class RepairCompleteView(APIView):
    """完成工单。"""

    def post(self, request, ticket_id):
        ticket = services.complete_ticket(ticket_id)
        return Response(RepairTicketSerializer(ticket, context={'request': request}).data)


class RepairStaffListView(APIView):
    """物业人员及其在手未完成工单数（升级转派依据）。"""

    def get(self, request):
        staff = RepairStaff.objects.annotate(
            unfinished_count=Count(
                'tickets',
                filter=Q(tickets__status__in=[REPAIR_STATUS_PENDING, REPAIR_STATUS_PROCESSING]),
            )
        ).order_by('id')
        return Response(RepairStaffSerializer(staff, many=True).data)
