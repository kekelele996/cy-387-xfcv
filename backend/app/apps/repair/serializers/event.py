from rest_framework import serializers

from ..models import TicketEvent


class TicketEventSerializer(serializers.ModelSerializer):
    """工单事件流水序列化，升级记录包含原处理人与新处理人。"""

    type = serializers.CharField(source='event_type')
    time = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M:%S')
    operatorName = serializers.SerializerMethodField()
    fromAssigneeName = serializers.SerializerMethodField()
    toAssigneeName = serializers.SerializerMethodField()

    class Meta:
        model = TicketEvent
        fields = ['id', 'type', 'time', 'operatorName', 'fromAssigneeName', 'toAssigneeName', 'remark']

    def get_operatorName(self, obj):
        return obj.operator.name if obj.operator else None

    def get_fromAssigneeName(self, obj):
        return obj.from_assignee.name if obj.from_assignee else None

    def get_toAssigneeName(self, obj):
        return obj.to_assignee.name if obj.to_assignee else None
