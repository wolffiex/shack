from django.utils import timezone
from django.shortcuts import redirect
from pushbyt.models import Animation
from django.db.models import Q, F
from django.views.decorators.cache import never_cache
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@never_cache
def get_preview(_):
    now = timezone.now()
    anims = get_next_animations(now)
    anim = choose_anim(anims)
    if anim:
        if anim.served_at:
            logger.error(
                f"Already served {anim.file_path} at {
                    anim.served_at} now {now}"
            )
    else:
        anim = Animation(start_time=Animation.align_time(now))
    anim.served_at = now
    anim.save()
    logger.info(f"Redirect {anim.url}")
    return redirect(anim.url)


def choose_anim(anims):
    logger.info(f"Choose {anims}")
    logger.info(f" hoose {len(anims)}")
    return anims.first()


def get_next_animations(now):
    return Animation.objects.filter(
        Q(start_time__isnull=True, served_at__isnull=True) |
        (Q(start_time__gt=now) &
         Q(start_time__lte=now + timedelta(seconds=15)))
    ).order_by(F('start_time').asc(nulls_first=True), 'created_at')
