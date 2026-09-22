from rest_framework.exceptions import APIException

from app.constants.errors import ERROR_MESSAGES


class BusinessError(APIException):
    """业务异常：错误码与文案统一来自 constants/errors.py。"""

    def __init__(self, code: str, status_code: int = 400):
        self.code = code
        self.status_code = status_code
        self.default_code = code
        super().__init__(ERROR_MESSAGES.get(code, code))
