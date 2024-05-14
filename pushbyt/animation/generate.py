import os
from datetime import datetime, timedelta
from pushbyt.animation.rays2 import clock_rays
from pushbyt.animation.song import song_info
from pathlib import Path
from django.utils import timezone
from pushbyt.models import Animation
from pushbyt.spotify import now_playing
from pushbyt.animation import render, FRAME_TIME
from typing import Optional
import logging


ANIM_DURATION = timedelta(seconds=15)
FRAME_COUNT = ANIM_DURATION / FRAME_TIME
RENDER_DIR = Path("render")


logger = logging.getLogger(__name__)


def generate():
    os.makedirs(RENDER_DIR, exist_ok=True)
    result = check_spotify() + "\n"
    result += generate_timed()
    return result

def generate_timed():
    end_time = get_last_animation_end_time()
    if not end_time:
        end_time = timezone.now()
    logger.info(f"last animation ends {end_time}")
    if end_time < timezone.now() + timedelta(seconds=90):
        generate_rays(end_time)
        return "Generated rays"
    return f"Already have timed content through {end_time}"

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


def get_last_animation_end_time() -> Optional[datetime]:
    try:
        last_animation = Animation.objects.filter(start_time__isnull=False).latest(
            "start_time"
        )
        return last_animation.start_time_local + timedelta(seconds=15)
    except Animation.DoesNotExist:
        return None


def generate_rays(start_time: datetime):
    t = Animation.align_time(start_time)
    end_time = t + timedelta(seconds=90)
    frames = clock_rays()
    next(frames)
    animations = []
    while t < end_time:
        anim_frames = []
        anim_start_time = t
        for _ in range(int(FRAME_COUNT)):
            time_str = t.strftime("%-I:%M")
            anim_frames.append(frames.send(time_str))
            t += FRAME_TIME
        file_path = (
            Path("render") / anim_start_time.strftime("%j-%H-%M-%S")
        ).with_suffix(".webp")
        render(anim_frames, file_path)
        animations.append(
            Animation(
                file_path=file_path,
                start_time=anim_start_time,
                source=Animation.Source.RAYS,
            )
        )
    Animation.objects.bulk_create(animations)