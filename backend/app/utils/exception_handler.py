from rest_framework.views import exception_handler as drf_exception_handler

from app.apps.repair.exceptions import RepairError


def standard_exception_handler(exc, context):
    # 报修模块业务异常：返回统一标准格式，并携带业务错误码。
    if isinstance(exc, RepairError):
        from rest_framework.response import Response
        return Response(
            {'success': False, 'code': exc.code, 'data': None, 'error': exc.message},
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    response.data = {'success': False, 'code': response.status_code, 'data': None, 'error': response.data}
    return response
