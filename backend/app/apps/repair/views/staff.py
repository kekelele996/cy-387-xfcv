"""物业人员列表：供接单身份选择和转派对象展示。"""
from rest_framework.response import Response
from rest_framework.views import APIView

from ..selectors import list_active_staff
from ..serializers import RepairStaffSerializer


class StaffListView(APIView):
    def get(self, request):
        staff = list_active_staff()
        return Response(RepairStaffSerializer(staff, many=True).data)
