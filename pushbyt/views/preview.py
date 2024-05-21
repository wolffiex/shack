from django.utils import timezone
from django.shortcuts import redirect
from pushbyt.models import Animation
from django.db.models import Q, F
from django.views.decorators.cache import never_cache
from datetime import timedelta, datetime
from functools import cmp_to_key
import logging

logger = logging.getLogger(__name__)


@never_cache
def get_preview(_):
    now = timezone.now()
    anims = get_animation_list(now)
    anim = choose_anim(list(anims), now) if anims else None
    if anim:
        if anim.served_at:
            logger.error(
                f"Already served {anim.file_path} at {
                    anim.served_at} now {now}"
            )
    else:
        anim = Animation()
    anim.served_at = now
    anim.save()
    logger.info(f"Redirect {anim.url}")
    return redirect(anim.url)


def time_str(maybe_time):
    maybe_timez = maybe_time and maybe_time.astimezone(
        timezone.get_current_timezone())
    return maybe_timez and maybe_time.strftime(" %-I:%M:%S")


def choose_anim(anims, now):
    logger.info(f"Choose anim at {time_str(now)} from list of {len(anims)}")
    anims.sort(key=cmp_to_key(lambda a1, a2: compare_animations(a1, a2, now)))
    for anim in anims:
        sa = time_str(anim.served_at)
        st = time_str(anim.start_time)
        logger.info(f"A {anim.source} {sa} {st} {anim.metadata}")
    return anims[0]


def get_animation_list(now):
    return Animation.objects.filter(
        Q(served_at__gte=now - timedelta(minutes=1))
        | Q(start_time__isnull=True, served_at__isnull=True)
        | Q(start_time__gt=now, start_time__lte=now + timedelta(seconds=30))
    ).order_by(
        F("served_at").asc(nulls_last=True),
        F("start_time").asc(nulls_first=True),
        "created_at",
    )


def compare_animations(
    anim1: Animation, anim2: Animation, now: datetime
) -> int:
    anims = [anim1, anim2]
    anim1_not_served, anim2_not_served = [not a.served_at for a in anims]
    if anim1_not_served != anim2_not_served:
        return -1 if anim1_not_served else 1
    elif not anim1_not_served:
        # Both have been served
        return -1 if anim1.served_at > anim2.served_at else 1

    # If we get here, neither animation was served
    anim1_door, anim2_door = [
        a.source == Animation.Source.DOORBELL for a in anims
    ]
    if anim1_door != anim2_door:
        # Case where they are both doorbell doesn't matter
        return -1 if anim1_door else 1

    anim1_no_start, anim2_no_start = [not a.start_time for a in anims]
    if anim1_no_start != anim2_no_start:
        return -1 if anim1_no_start else 1

    # todo: choose between rays and timer
    return 0
