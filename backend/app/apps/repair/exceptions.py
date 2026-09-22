from app.constants.errors import ERROR_CODES, ERROR_MESSAGES


class RepairError(Exception):
    """报修模块业务异常，由 DRF 自定义异常处理统一封装。"""

    def __init__(self, code: str, status_code: int = 400):
        self.code = ERROR_CODES[code]
        self.message = ERROR_MESSAGES[code]
        self.status_code = status_code
        super().__init__(self.message)
