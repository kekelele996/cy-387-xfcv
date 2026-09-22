from django.apps import AppConfig


class RepairConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.apps.repair'

    def ready(self):
        from django.conf import settings
        from django.db.backends.signals import connection_created

        # 仅本地 SQLite 需要：WAL 提升读写并发，busy_timeout 让写锁竞争时等待而非立即报错。
        if 'sqlite' not in settings.DATABASES['default']['ENGINE']:
            return

        def _enable_sqlite_pragmas(sender, connection, **kwargs):
            if connection.vendor != 'sqlite':
                return
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA busy_timeout=20000')

        connection_created.connect(_enable_sqlite_pragmas)
