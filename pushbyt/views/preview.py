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
    anims = get_animation_list(now)
    anim = choose_anim(anims, now)
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


def time_str(maybe_time):
    maybe_timez = maybe_time and maybe_time.astimezone(timezone.get_current_timezone())
    return maybe_timez and maybe_time.strftime(" %-I:%M:%S")


def choose_anim(anims, now):
    logger.info(f"Choose anim at {time_str(now)} from list of {len(anims)}")
    choice = None
    for anim in anims:
        sa = time_str(anim.served_at)
        st = time_str(anim.start_time)
        logger.info(
            f"A {anim.source} {anim.metadata} {sa} {st}"
        )
        if not anim.served_at and not choice:
            choice = anim
    return choice



def get_animation_list(now):
    return Animation.objects.filter(
        Q(served_at__gte=now - timedelta(minutes=1))
        | Q(start_time__isnull=True, served_at__isnull=True)
        | Q(start_time__gt=now, start_time__lte=now + timedelta(minutes=30))
    ).order_by(
        F("served_at").asc(nulls_last=True),
        F("start_time").asc(nulls_first=True),
        "created_at",
    )
