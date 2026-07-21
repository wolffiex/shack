from django.apps import AppConfig
import logging
import threading

logger = logging.getLogger(__name__)


class PushbytConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pushbyt"

    def ready(self):
        """Clear any stale locks when the application starts."""
        # Only run once per process (not during migrations or management commands)
        import sys

        if "runserver" not in sys.argv and "gunicorn" not in sys.argv[0]:
            return

        # Use a thread with a small delay to avoid database access during app init
        # This prevents Django's "database access during initialization" warning
        def clear_locks_delayed():
            import time

            time.sleep(0.5)  # Wait for Django to fully initialize

            from django.db import transaction
            from pushbyt.models import Lock

            try:
                # Use select_for_update to ensure only one worker clears locks
                with transaction.atomic():
                    locks = Lock.objects.select_for_update(nowait=True).filter(
                        acquired=True
                    )
                    count = locks.count()
                    if count > 0:
                        locks.update(acquired=False)
                        logger.warning(f"Cleared {count} stale lock(s) on startup")
            except Exception as e:
                # If another worker is already clearing, or database not ready, silently continue
                # This is expected behavior when multiple workers start simultaneously
                logger.debug(f"Lock clearing skipped: {e}")
                pass

        thread = threading.Thread(target=clear_locks_delayed, daemon=True)
        thread.start()
