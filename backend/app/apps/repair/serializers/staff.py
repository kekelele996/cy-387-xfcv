from rest_framework import serializers

from ..models import RepairStaff


class RepairStaffSerializer(serializers.ModelSerializer):
    """物业人员序列化。"""

    openCount = serializers.SerializerMethodField()

    class Meta:
        model = RepairStaff
        fields = ['id', 'name', 'phone', 'is_active', 'openCount']

    def get_openCount(self, obj):
        return getattr(obj, 'open_count', None)
