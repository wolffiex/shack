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
from django.utils import timezone
from pushbyt.models import Animation
from pushbyt.spotify import now_playing
from pushbyt.animation import render, FRAME_TIME
from ha.models import Timer
import logging


ANIM_DURATION = timedelta(seconds=15)
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


def generate_timer(start_time, timer):
    segment_start = get_segment_start(start_time, Animation.Source.TIMER)
    if not segment_start:
        return "Already have timers"
    t = segment_start
    end_time = t + SEGMENT_TIME
    frames = timer_frames(timer.created_at + timer.duration - segment_start)
    animations = []
    while t < end_time:
        anim_frames = islice(frames, int(FRAME_COUNT))
        important = timer.created_at + timer.duration - t < timedelta(seconds=90)
        file_path = (
            Path("render") / ("timer_" + t.strftime("%j-%H-%M-%S"))
        ).with_suffix(".webp")
        if not render(anim_frames, file_path):
            break
        animations.append(
            Animation(
                file_path=file_path,
                start_time=t,
                source=Animation.Source.TIMER,
                metadata={"id": timer.pk, "important": important},
            )
        )
        t += FRAME_COUNT * FRAME_TIME
    new_anims = Animation.objects.bulk_create(animations)
    return f"Created {len(new_anims)} timers starting at " + segment_start.strftime(
        " %-I:%M:%S"
    )


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

SOURCES = [Animation.Source.RAYS, Animation.Source.RADAR]

def generate_clock(start_time: datetime):
    segment_start = get_segment_start(start_time, *SOURCES)
    if not segment_start:
        return "Already have clock"

    t = segment_start
    end_time = t + SEGMENT_TIME

    # Randomly choose between rays or radar
    source = random.choice(SOURCES)
    is_radar = source == Animation.Source.RADAR

    # Choose the appropriate animation generator based on the selected source
    frames = clock_radar() if is_radar else clock_rays()

    next(frames)
    animations = []
    while t < end_time:
        anim_frames = []
        anim_start_time = t;
        for _ in range(int(FRAME_COUNT)):
            anim_frames.append(frames.send(t))
            t += FRAME_TIME
        file_path = (
            Path("render") / ("ray_" + anim_start_time.strftime("%j-%H-%M-%S"))
        ).with_suffix(".webp")
        render(anim_frames, file_path)
        animations.append(
            Animation( 
                file_path=file_path,
                start_time=anim_start_time,
                source=Animation.Source.RAYS,
            )
        )
    new_anims = Animation.objects.bulk_create(animations)
    return f"Created {len(new_anims)} {'radar' if is_radar else 'rays'} starting at " + segment_start.strftime(
        " %-I:%M:%S"
    )


def update_timer():
    now = timezone.now().astimezone(timezone.get_current_timezone())
    aligned_time = Animation.align_time(now)
    return check_timer(aligned_time)
