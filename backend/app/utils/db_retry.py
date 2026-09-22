import time
from functools import wraps

from django.db import OperationalError

from app.utils.logger import get_logger

logger = get_logger('db')


def retry_on_db_lock(max_attempts: int = 5, delay: float = 0.05):
    """数据库写锁冲突时重试。

    PostgreSQL 下 select_for_update 让并发请求等待行锁，一般不会触发；
    SQLite 本地开发在写事务冲突时可能立即抛出 database is locked，短暂退避后重试即可。
    重试仅针对锁类 OperationalError，业务异常不受影响。
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except OperationalError as exc:
                    last_error = exc
                    if 'locked' not in str(exc).lower() and 'lock' not in str(exc).lower():
                        raise
                    if attempt == max_attempts - 1:
                        break
                    sleep_for = delay * (2 ** attempt)
                    logger.info('db lock in %s, retry %s/%s after %.2fs',
                                func.__name__, attempt + 1, max_attempts - 1, sleep_for)
                    time.sleep(sleep_for)
            raise last_error

        return wrapper

    return decorator
