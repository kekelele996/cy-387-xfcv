"""报修分级响应时限。"""
from datetime import timedelta

from app.constants.enums import REPAIR_RESPONSE_LIMIT_MINUTES
from app.constants.errors import ERROR_CODES
from app.utils.errors import BusinessError


def get_response_limit_minutes(fault_type: str) -> int:
    """水电、门锁 30 分钟；管道、家电、其他 4 小时。"""
    try:
        return REPAIR_RESPONSE_LIMIT_MINUTES[fault_type]
    except KeyError:
        raise BusinessError(ERROR_CODES['REPAIR_INVALID'], status_code=400)


def calc_response_deadline(fault_type: str, submitted_at):
    """根据故障类型计算响应截止时间。"""
    return submitted_at + timedelta(minutes=get_response_limit_minutes(fault_type))
