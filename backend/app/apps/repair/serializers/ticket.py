from rest_framework import serializers

from app.constants.enums import REPAIR_TYPES
from ..models import RepairTicket
from .event import TicketEventSerializer


class RepairTicketCreateSerializer(serializers.Serializer):
    """住户提交报修入参校验。"""

    faultType = serializers.ChoiceField(choices=REPAIR_TYPES)
    description = serializers.CharField(max_length=500)
    submitterName = serializers.CharField(max_length=40, required=False, allow_blank=True, default='')
    photo = serializers.ImageField(required=False, allow_null=True)


class RepairTicketSerializer(serializers.ModelSerializer):
    """报修工单序列化：含分级时限、计时、处理人及完整事件流水。"""

    faultType = serializers.CharField(source='fault_type')
    submitterName = serializers.CharField(source='submitter_name')
    assigneeId = serializers.IntegerField(source='assignee_id')
    assigneeName = serializers.SerializerMethodField()
    responseLimitMinutes = serializers.SerializerMethodField()
    deadline = serializers.DateTimeField(source='response_deadline', format='%Y-%m-%d %H:%M:%S')
    createdAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M:%S')
    acceptedAt = serializers.DateTimeField(source='accepted_at', format='%Y-%m-%d %H:%M:%S')
    completedAt = serializers.DateTimeField(source='completed_at', format='%Y-%m-%d %H:%M:%S')
    isOverdue = serializers.SerializerMethodField()
    photoUrl = serializers.SerializerMethodField()
    events = TicketEventSerializer(many=True, read_only=True)

    class Meta:
        model = RepairTicket
        fields = [
            'id', 'faultType', 'description', 'photoUrl', 'submitterName',
            'status', 'assigneeId', 'assigneeName',
            'responseLimitMinutes', 'deadline', 'createdAt', 'acceptedAt', 'completedAt',
            'escalated', 'isOverdue', 'events',
        ]

    def get_assigneeName(self, obj):
        return obj.assignee.name if obj.assignee else None

    def get_responseLimitMinutes(self, obj):
        from app.constants.enums import REPAIR_RESPONSE_LIMIT_MINUTES
        return REPAIR_RESPONSE_LIMIT_MINUTES[obj.fault_type]

    def get_isOverdue(self, obj):
        annotated = getattr(obj, 'is_overdue_annotation', None)
        if annotated is not None:
            return annotated
        return obj.is_overdue

    def get_photoUrl(self, obj):
        if not obj.photo:
            return None
        request = self.context.get('request')
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url
