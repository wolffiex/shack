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
                f"Already served {anim.file_path} at {anim.served_at} now {now}"
            )
    else:
        anim = Animation()
    anim.served_at = now
    anim.save()
    logger.info(f"Redirect {anim.url}")
    return redirect(anim.url)


def time_str(maybe_time):
    """Convert a datetime to a localized time string in current timezone."""
    if not maybe_time:
        return None
    # Convert to current timezone
    localized_time = maybe_time.astimezone(timezone.get_current_timezone())
    # Format the localized time, not the original time
    return localized_time.strftime(" %-I:%M:%S")


def choose_anim(anims, now: datetime):
    logger.info(f"Choose anim at {time_str(now)} from list of {len(anims)}")
    summary = summarize_anims(anims, now)

    # Filter out timer and doorbell animations that have already been served
    # This prevents the same timer or doorbell from being displayed multiple times
    filtered_anims = [
        a
        for a in anims
        if not (
            (
                a.source == Animation.Source.TIMER
                or a.source == Animation.Source.DOORBELL
            )
            and a.served_at is not None
        )
    ]

    # If we filtered everything out (e.g., only timer animations that were already served),
    # fall back to original list - but this should be rare
    if not filtered_anims:
        logger.warning("All animations filtered out, using original list as fallback")
        filtered_anims = anims

    filtered_anims.sort(key=cmp_to_key(partial(compare_animations, summary=summary)))
    for anim in filtered_anims:
        sa = time_str(anim.served_at)
        st = time_str(anim.start_time)
        logger.info(f"A {anim.source} {anim.pk} {sa} {st} {anim.metadata}")

    return filtered_anims[0]


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
    last_clock = None
    for anim in [a for a in anims if a.served_at]:
        if is_timer(anim):
            last_timer = anim
        elif is_clock(anim):
            last_clock = anim
    return {
        "now": now,
        "last_timer": last_timer,
        "last_clock": last_clock,
    }


def is_timer(anim):
    return anim.source == Animation.Source.TIMER


def is_clock(anim):
    return anim.source in [Animation.Source.RAYS, Animation.Source.RADAR]


def is_served(animation):
    return animation.served_at is not None


def is_important_and_soon(animation, now):
    is_important = animation.metadata.get("important", False)
    return is_important and (
        not animation.start_time or animation.start_time - now < timedelta(seconds=15)
    )


def compare_animations(anim1: Animation, anim2: Animation, summary) -> int:
    """
    Compare two animations to determine priority order for display on the Tidbyt device.

    This is the core prioritization function that decides which animation should be displayed.
    It implements a strict multi-level priority system with the following hierarchy:

    1. Doorbell animations (absolute highest priority, critical alerts)
    2. Unserved real-time content (new content without a start_time that hasn't been shown yet)
    3. Upcoming unserved timed animations (new scheduled content, sorted by earliest start time)
    4. Most recently served animations (prioritizing animations with the most recent served_at time)
       - This ensures animations maintain visibility and aren't interrupted prematurely
       - Ensures consistent viewing experience when animations span multiple requests
    5. For animations with equal priority at the levels above:
       - Important animations (metadata with important=True)
       - Earlier scheduled start times
       - Content type balancing (timers and clocks are shown periodically)

    This priority system gives precedence to critical notifications and new content,
    while ensuring already-displayed animations continue to be shown for proper visibility.

    Note: Timer and doorbell animations that have already been served are filtered out
    before reaching this comparison function to prevent showing the same timer or doorbell
    notification multiple times.

    Args:
        anim1: First animation to compare
        anim2: Second animation to compare
        summary: Dictionary containing context info like current time and last shown content types

    Returns:
        -1 if anim1 should be displayed before anim2
         1 if anim2 should be displayed before anim1
         0 if they have equal priority (extremely rare)
    """

    def compare_by_predicate(pred):
        nonlocal anim1, anim2
        p1, p2 = pred(anim1), pred(anim2)
        return 0 if p1 == p2 else -1 if p1 else 1

    now = summary["now"]

    # Priority 1: Doorbell notifications (highest priority)
    doorbell_1 = anim1.source == Animation.Source.DOORBELL
    doorbell_2 = anim2.source == Animation.Source.DOORBELL
    if doorbell_1 != doorbell_2:
        return -1 if doorbell_1 else 1

    # Priority 2: New real-time content (unserved with no scheduled time)
    unserved_realtime_1 = not is_served(anim1) and anim1.start_time is None
    unserved_realtime_2 = not is_served(anim2) and anim2.start_time is None
    if unserved_realtime_1 != unserved_realtime_2:
        return -1 if unserved_realtime_1 else 1

    # Check for important timer animations first
    important1 = is_important_and_soon(anim1, now)
    important2 = is_important_and_soon(anim2, now)
    if important1 != important2:
        return -1 if important1 else 1

    # Priority 3: New scheduled content (unserved with start_time)
    unserved_upcoming_1 = not is_served(anim1) and anim1.start_time is not None
    unserved_upcoming_2 = not is_served(anim2) and anim2.start_time is not None

    # Check for unserved timer animations - prioritize timers if we haven't shown one recently
    if unserved_upcoming_1 and unserved_upcoming_2:
        # Both are unserved scheduled animations
        timer1 = is_timer(anim1)
        timer2 = is_timer(anim2)

        # If one is a timer and the other isn't, and we haven't shown a timer recently,
        # prioritize the timer animation
        if timer1 != timer2 and not summary.get("last_timer"):
            return -1 if timer1 else 1

        # Both are new scheduled content, so compare by earliest start time
        return -1 if anim1.start_time < anim2.start_time else 1

    # If only one is new scheduled content, prefer it
    if unserved_upcoming_1 != unserved_upcoming_2:
        return -1 if unserved_upcoming_1 else 1

    # Priority 4: Most recently served animations
    if is_served(anim1) and is_served(anim2):
        # Prefer the most recently served animation for visibility consistency
        return -1 if anim1.served_at > anim2.served_at else 1

    # Priority 5: Additional criteria for edge cases and tie-breaking
    predicates = [
        # Priority 5a: Important animations (like final timer countdowns)
        # These should have higher priority regardless of content balancing
        lambda a: is_important_and_soon(a, now),
    ]

    # Priority 5b: Earlier scheduled start times when both have start times
    if anim1.start_time and anim2.start_time:
        min_start_time = min(anim1.start_time, anim2.start_time)
        predicates.append(lambda a: a.start_time == min_start_time)

    # Priority 5c: Content type balancing (ensure variety)
    # Show timers if none shown recently
    if not summary["last_timer"]:
        predicates.append(is_timer)

    # Show clocks if none shown recently
    if not summary["last_clock"]:
        predicates.append(is_clock)

    # Apply predicates in order and return first non-zero result
    return next(filter(lambda r: r != 0, map(compare_by_predicate, predicates)), 0)
