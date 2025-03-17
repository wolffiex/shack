import os
import random
from datetime import datetime, timedelta
from itertools import islice
from pushbyt.animation.rays2 import clock_rays
from pushbyt.animation.radar import clock_radar
from pushbyt.animation.song import song_info
from pushbyt.animation.timer import timer as timer_frames
from pathlib import Path
from django.db.models import Max
from django.db import utils as django_db_utils
from django.utils import timezone
from pushbyt.models import Animation
from pushbyt.spotify import now_playing
from pushbyt.animation import render, FRAME_TIME
from ha.models import Timer
import logging


ANIM_DURATION = timedelta(seconds=15)
ANIM_STEP = timedelta(seconds=10)  # Start a new animation every 10 seconds
FRAME_COUNT = ANIM_DURATION // FRAME_TIME
RENDER_DIR = Path("render")


logger = logging.getLogger(__name__)


def generate():
    os.makedirs(RENDER_DIR, exist_ok=True)
    now = timezone.now().astimezone(timezone.get_current_timezone())
    logger.info(f"now {now}")
    aligned_time = Animation.align_time(now)
    logger.info(f"aligned {aligned_time}")
    results = [
        check_spotify(),
        check_timer(aligned_time),
        generate_clock(aligned_time),
    ]
    return "\n".join(results)


def check_spotify():
    track_info = now_playing()
    if not track_info:
        return "Spotify not playing"

    logger.info(track_info)
    track_id = track_info["id"]
    track_title = track_info["title"]
    try:
        last_spotify = Animation.objects.filter(source=Animation.Source.SPOTIFY).latest(
            "created_at"
        )
        if last_spotify.metadata["id"] == track_id:
            logger.info(f"Already did {track_title}")
            return f"Spotify already did {track_title}"
    except Animation.DoesNotExist:
        pass

    frames = [*song_info(track_title, track_info["artist"], track_info["art"])]
    file_path = (Path("render") / f"spotify-{track_id}").with_suffix(".webp")
    render(frames, file_path)
    anim = Animation(
        file_path=file_path, source=Animation.Source.SPOTIFY, metadata={"id": track_id}
    )
    anim.save()
    return f"Spotify now playing {track_title}"


SEGMENT_TIME = timedelta(seconds=90)


def check_timer(start_time):
    timer = Timer.objects.order_by("-created_at").first()
    timer_animations = Animation.objects.filter(
        source=Animation.Source.TIMER,
        start_time__gte=start_time,
    )
    results = []
    if timer and timer.is_running:
        timer_animations = timer_animations.exclude(metadata__id=timer.pk)

    delete_result = timer_animations.delete()
    results.append(f"Deleted old timers {delete_result}")

    if timer and timer.is_running:
        render_result = generate_timer(start_time, timer)
        results.append(render_result)

    return "\n".join(results)


def generate_timer_frames(start_time, timer, duration):
    """Generate a continuous sequence of timer frames."""
    t = start_time
    end_time = t + duration

    # Calculate the time remaining from the start of our sequence
    time_remaining_at_start = timer.created_at + timer.duration - t

    # Generate all frames
    all_frames = []
    all_times = []

    # Create a new generator that starts from our specific time point
    frames = timer_frames(time_remaining_at_start)

    while t < end_time:
        try:
            frame = next(frames)
            all_frames.append(frame)
            all_times.append(t)
            t += FRAME_TIME
        except StopIteration:
            # Timer might end during the sequence
            break

    return all_frames, all_times


def generate_timer(start_time, timer):
    segment_start = get_segment_start(start_time, Animation.Source.TIMER)
    if not segment_start:
        return "Already have timers"

    # Generate frames for full segment plus buffer
    duration = SEGMENT_TIME + ANIM_DURATION
    all_frames, all_times = generate_timer_frames(segment_start, timer, duration)

    # No frames were generated (timer might be too short)
    if not all_frames:
        return "No timer frames generated"

    animations = []
    frames_per_anim = int(ANIM_DURATION.total_seconds() / FRAME_TIME.total_seconds())
    frames_per_step = int(ANIM_STEP.total_seconds() / FRAME_TIME.total_seconds())

    # Make sure we have enough frames for a complete animation
    max_start_idx = len(all_frames) - frames_per_anim

    for i in range(0, max_start_idx + 1, frames_per_step):
        anim_frames = all_frames[i : i + frames_per_anim]
        anim_start_time = all_times[i]

        # Check if this timer is approaching completion (important)
        important = timer.created_at + timer.duration - anim_start_time < timedelta(
            seconds=90
        )

        file_path = (
            Path("render") / ("timer_" + anim_start_time.strftime("%j-%H-%M-%S"))
        ).with_suffix(".webp")

        if render(anim_frames, file_path):
            animations.append(
                Animation(
                    file_path=file_path,
                    start_time=anim_start_time,
                    source=Animation.Source.TIMER,
                    metadata={"id": timer.pk, "important": important},
                )
            )

    try:
        new_anims = Animation.objects.bulk_create(animations)
        return f"Created {len(new_anims)} timers starting at " + segment_start.strftime(
            " %-I:%M:%S"
        )
    except django_db_utils.IntegrityError as e:
        # Log the error but don't crash
        logger.warning(
            f"Some timer animations were not created due to uniqueness constraints: {e}"
        )
        return f"Partial creation of timer animations - some already existed"


def get_segment_start(start_time, *sources):
    # For now, assume all animations are continuous.
    # This is not a hard guarantee
    max_start_time = Animation.objects.filter(
        start_time__gte=start_time, source__in=sources
    ).aggregate(max_start_time=Max("start_time"))["max_start_time"]

    return (
        Animation.next_time(max_start_time.astimezone(timezone.get_current_timezone()))
        if max_start_time
        else start_time
    )


CLOCK_SOURCES = [Animation.Source.RAYS, Animation.Source.RADAR]


def generate_clock_frames(start_time: datetime, duration: timedelta, source):
    """Generate a continuous sequence of clock frames."""
    t = start_time
    end_time = t + duration

    # Choose the appropriate animation generator based on the selected source
    frames_generator = (
        clock_radar(t) if source == Animation.Source.RADAR else clock_rays()
    )

    # Start the generator
    next(frames_generator)

    # Generate all frames
    all_frames = []
    all_times = []
    while t < end_time:
        all_frames.append(frames_generator.send(t))
        all_times.append(t)
        t += FRAME_TIME

    return all_frames, all_times


def slice_into_animations(
    all_frames, all_times, source, anim_duration=ANIM_DURATION, step=ANIM_STEP
):
    """Slice frames into overlapping animations."""
    frames_per_anim = int(anim_duration.total_seconds() / FRAME_TIME.total_seconds())
    frames_per_step = int(step.total_seconds() / FRAME_TIME.total_seconds())

    animations = []
    # Make sure we have enough frames for a complete animation
    max_start_idx = len(all_frames) - frames_per_anim

    for i in range(0, max_start_idx + 1, frames_per_step):
        anim_frames = all_frames[i : i + frames_per_anim]
        anim_start_time = all_times[i]

        file_path = (
            Path("render") / (f"{source}_" + anim_start_time.strftime("%j-%H-%M-%S"))
        ).with_suffix(".webp")

        render(anim_frames, file_path)

        animations.append(
            Animation(
                file_path=file_path,
                start_time=anim_start_time,
                source=source,
            )
        )

    return animations


def generate_clock(start_time: datetime):
    segment_start = get_segment_start(start_time, *CLOCK_SOURCES)
    if not segment_start:
        return "Already have clock"

    # Randomly choose between rays or radar
    source = random.choice(CLOCK_SOURCES)

    # Generate frames for 90 seconds plus buffer to ensure we have enough frames
    # for the last complete animation
    duration = SEGMENT_TIME + ANIM_DURATION
    all_frames, all_times = generate_clock_frames(segment_start, duration, source)

    # Slice into overlapping animations
    animations = slice_into_animations(all_frames, all_times, source)

    # Save to database - handle potential uniqueness constraint errors
    try:
        new_anims = Animation.objects.bulk_create(animations)
        return (
            f"Created {len(new_anims)} {source} starting at "
            + segment_start.strftime(" %-I:%M:%S")
        )
    except django.db.utils.IntegrityError as e:
        # Log the error but don't crash
        logger.warning(
            f"Some animations were not created due to uniqueness constraints: {e}"
        )
        return f"Partial creation of {source} animations - some already existed"


def update_timer():
    now = timezone.now().astimezone(timezone.get_current_timezone())
    aligned_time = Animation.align_time(now)
    return check_timer(aligned_time)
