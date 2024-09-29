from django.utils import timezone
from django.shortcuts import redirect
from pushbyt.models import Animation
from django.db.models import Q, F
from django.views.decorators.cache import never_cache
from datetime import timedelta, datetime
from functools import partial
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
    maybe_timez = maybe_time and maybe_time.astimezone(timezone.get_current_timezone())
    return maybe_timez and maybe_time.strftime(" %-I:%M:%S")


def choose_anim(anims, now: datetime):
    logger.info(f"Choose anim at {time_str(now)} from list of {len(anims)}")
    summary = summarize_anims(anims, now)
    anims.sort(key=cmp_to_key(partial(compare_animations, summary=summary)))
    for anim in anims:
        sa = time_str(anim.served_at)
        st = time_str(anim.start_time)
        logger.info(f"A {anim.source} {anim.pk} {sa} {st} {anim.metadata}")
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


def summarize_anims(anims, now):
    last_timer = None
    last_ray = None
    for anim in [a for a in anims if a.served_at]:
        if is_timer(anim):
            last_timer = anim
        elif is_ray(anim):
            last_ray = anim
    return {
        "now": now,
        "last_timer": last_timer,
        "last_ray": last_ray,
    }


def is_timer(anim):
    return anim.source == Animation.Source.TIMER


def is_ray(anim):
    return anim.source == Animation.Source.RAYS


def is_served(animation):
    return animation.served_at is not None


def is_important_and_soon(animation, now):
    is_important = animation.metadata.get("important", False)
    return is_important and (
        not animation.start_time or animation.start_time - now < timedelta(seconds=15)
    )


def compare_animations(anim1: Animation, anim2: Animation, summary) -> int:
    def compare_by_predicate(pred):
        nonlocal anim1, anim2
        p1, p2 = pred(anim1), pred(anim2)
        return 0 if p1 == p2 else -1 if p1 else 1

    if is_served(anim1) and is_served(anim2):
        return -1 if anim1.served_at > anim2.served_at else 1

    predicates = [
        # unserved before served
        lambda a: not is_served(a),
        # doorbell before everything
        lambda a: a.source == Animation.Source.DOORBELL,
        # metadata with important: True
        lambda a: is_important_and_soon(a, summary["now"]),
        # ephemeral content
        lambda a: a.start_time is None,
    ]

    if anim1.start_time and anim2.start_time:
        min_start_time = min(anim1.start_time, anim2.start_time)
        predicates.append(lambda a: a.start_time == min_start_time)

    if not summary["last_timer"]:
        predicates.append(is_timer)

    if not summary["last_ray"]:
        predicates.append(is_ray)

    return next(filter(lambda r: r != 0, map(compare_by_predicate, predicates)), 0)
