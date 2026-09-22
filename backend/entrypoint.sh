#!/bin/sh
set -e

# 等待数据库就绪后执行迁移
python manage.py migrate --noinput

# 后台周期扫描超时未接单工单并升级（每个工单只会升级一次，重复扫描安全）
(
  while true; do
    sleep 60
    python manage.py escalate_overdue >/dev/null 2>&1 || true
  done
) &

exec gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 3
