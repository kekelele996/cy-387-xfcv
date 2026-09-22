from rest_framework.views import exception_handler

from app.utils.logger import get_logger

logger = get_logger('api')


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = getattr(exc, 'code', None) or response.status_code
    detail = response.data
    if isinstance(detail, dict) and 'detail' in detail:
        detail = detail['detail']

    logger.warning('api error: %s %s -> %s', context.get('request.method'), context.get('request.path'), detail)
    response.data = {'success': False, 'code': code, 'data': None, 'error': detail}
    return response
