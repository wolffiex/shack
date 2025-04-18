from django.db import transaction, OperationalError
from django.http import HttpResponse
from pushbyt.models import Lock
from pushbyt.animation import generate as generate_animation
from django.utils import timezone
from pushbyt.models import Animation
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)


def generate(_):
    lock_name = "generate"

    try:
        # First, ensure the lock record exists (outside the transaction)
        Lock.objects.get_or_create(name=lock_name, defaults={"acquired": False})

        # Now try to acquire the lock in a separate transaction
        with transaction.atomic():
            try:
                lock = Lock.objects.select_for_update(nowait=True).get(name=lock_name)
                if lock.acquired:
                    logger.info("Generation already in progress, skipping")
                    return HttpResponse("Endpoint is already running", status=409)
                lock.acquired = True
                lock.save()
            except Lock.DoesNotExist:
                # This shouldn't happen since we created it above, but just in case
                logger.error("Lock disappeared during acquisition - race condition")
                return HttpResponse("Lock acquisition error", status=500)
    except OperationalError:
        logger.warning(
            "Lock contention detected, another process is generating animations"
        )
        return HttpResponse("Failed to acquire lock", status=500)

    result = "Exception"
    try:
        if is_running():
            result = generate_animation()
        else:
            result = "Not running"
    finally:
        with transaction.atomic():
            lock.acquired = False
            lock.save()

    logger.info(f"generate {result}")
    return HttpResponse(result)


def is_running() -> bool:
    now = timezone.localtime()

    one_minute_ago = now - timedelta(minutes=1)

    # If we haven't gotten a request in the last minute, then don't generate
    return Animation.objects.filter(served_at__gt=one_minute_ago).exists()
