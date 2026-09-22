from rest_framework import serializers

from app.constants.enums import REPAIR_TYPES, RESPONSE_DEADLINE_MINUTES
from .models import RepairEvent, RepairStaff, RepairTicket
from .services import is_overdue


class RepairStaffSerializer(serializers.ModelSerializer):
    unfinishedCount = serializers.SerializerMethodField()

    class Meta:
        model = RepairStaff
        fields = ['id', 'name', 'phone', 'unfinishedCount']

    def get_unfinishedCount(self, obj):
        return getattr(obj, 'unfinished_count', 0)


class RepairEventSerializer(serializers.ModelSerializer):
    operatorName = serializers.CharField(source='operator.name', default='', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', format='iso-8601', read_only=True)

    class Meta:
        model = RepairEvent
        fields = ['id', 'eventType', 'operatorName', 'detail', 'createdAt']

    eventType = serializers.CharField(source='event_type', read_only=True)


class RepairTicketSerializer(serializers.ModelSerializer):
    faultType = serializers.CharField(source='fault_type')
    photo = serializers.ImageField(required=False, allow_null=True)
    residentName = serializers.CharField(source='resident_name', required=False, allow_blank=True, default='')
    residentPhone = serializers.CharField(source='resident_phone', required=False, allow_blank=True, default='')
    status = serializers.CharField(read_only=True)
    submittedAt = serializers.DateTimeField(source='submitted_at', format='iso-8601', read_only=True)
    responseDeadline = serializers.DateTimeField(source='response_deadline', format='iso-8601', read_only=True)
    acceptedAt = serializers.DateTimeField(source='accepted_at', format='iso-8601', read_only=True)
    escalatedAt = serializers.DateTimeField(source='escalated_at', format='iso-8601', read_only=True)
    completedAt = serializers.DateTimeField(source='completed_at', format='iso-8601', read_only=True)
    assigneeId = serializers.IntegerField(source='assignee_id', read_only=True)
    assigneeName = serializers.CharField(source='assignee.name', default='', read_only=True)
    previousAssigneeName = serializers.CharField(source='previous_assignee.name', default='', read_only=True)
    deadlineMinutes = serializers.SerializerMethodField()
    overdue = serializers.SerializerMethodField()
    events = RepairEventSerializer(many=True, read_only=True)
    photoUrl = serializers.SerializerMethodField()

    class Meta:
        model = RepairTicket
        fields = [
            'id', 'faultType', 'description', 'photo', 'photoUrl',
            'residentName', 'residentPhone', 'status',
            'submittedAt', 'responseDeadline', 'acceptedAt', 'escalatedAt', 'completedAt',
            'deadlineMinutes', 'overdue', 'escalated',
            'assigneeId', 'assigneeName', 'previousAssigneeName',
            'events',
        ]

    def get_deadlineMinutes(self, obj):
        return RESPONSE_DEADLINE_MINUTES[obj.fault_type]

    def get_overdue(self, obj):
        return is_overdue(obj)

    def get_photoUrl(self, obj):
        if not obj.photo:
            return ''
        request = self.context.get('request')
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url

    def validate_faultType(self, value):
        if value not in REPAIR_TYPES:
            raise serializers.ValidationError('故障类型不合法')
        return value

    def validate_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('请填写故障描述')
        return value.strip()
