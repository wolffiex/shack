from django.db import transaction, OperationalError
from django.http import HttpResponse
from pushbyt.models import Lock
from pushbyt.animation import generate as generate_animation
from pushbyt.animation.generate import CLOCK_SOURCES
from django.utils import timezone
from pushbyt.models import Animation
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)


def parse_clock_source(request):
    """Optional ?source=rays|radar; None means random. Bad values are ignored,
    not rejected -- this is a background command."""
    requested = request.GET.get("source")
    if not requested:
        return None
    if requested not in {s.value for s in CLOCK_SOURCES}:
        logger.warning(f"Ignoring unusable clock source {requested!r}")
        return None
    return Animation.Source(requested)


def generate(request):
    lock_name = "generate"

    try:
        # Outside the transaction, so the row exists to be locked below.
        Lock.objects.get_or_create(name=lock_name, defaults={"acquired": False})

        with transaction.atomic():
            try:
                lock = Lock.objects.select_for_update(nowait=True).get(name=lock_name)
                if lock.acquired:
                    logger.info("Generation already in progress, skipping")
                    return HttpResponse("Endpoint is already running", status=409)
                lock.acquired = True
                lock.save()
            except Lock.DoesNotExist:
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
            result = generate_animation(parse_clock_source(request))
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

    return Animation.objects.filter(served_at__gt=one_minute_ago).exists()
