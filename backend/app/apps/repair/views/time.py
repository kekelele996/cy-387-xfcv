"""服务器时间：前端据此校正本地时钟偏差，保证倒计时与服务端超时判定一致。"""
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView


class ServerTimeView(APIView):
    def get(self, request):
        return Response({'now': timezone.now().isoformat()})
