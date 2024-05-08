from django.db import transaction, OperationalError
from django.http import HttpResponse
from pushbyt.models import Lock
from typing import Optional
import os
import tempfile
import subprocess
from PIL import Image
from datetime import datetime, timedelta
from pushbyt.animation.rays2 import clock_rays
from pathlib import Path
from django.utils import timezone
from pushbyt.models import Animation
from ha.utils import tidbyt_turn_on
import logging


FRAME_TIME = timedelta(milliseconds=100)
ANIM_DURATION = timedelta(seconds=15)
FRAME_COUNT = ANIM_DURATION / FRAME_TIME
RENDER_DIR = Path("render")


logger = logging.getLogger(__name__)

def generate(_):
    lock_name = "generate"

    try:
        with transaction.atomic():
            lock, _ = Lock.objects.select_for_update(nowait=True).get_or_create(name=lock_name)
            if lock.acquired:
                return HttpResponse("Endpoint is already running", status=409)
            lock.acquired = True
            lock.save()
    except OperationalError:
        return HttpResponse("Failed to acquire lock", status=500)

    try:
        if is_running():
            start_time = get_next_animation_time()
            logger.info(f'next animation time {start_time}')
            if start_time:
                generate_filler(start_time)
        else:
            if is_present():
                os.makedirs(RENDER_DIR, exist_ok=True)
                generate_welcome()
                tidbyt_turn_on()


        return HttpResponse("Generated successfully")
    finally:
        with transaction.atomic():
            lock.acquired = False
            lock.save()

def is_running() -> bool:
    now = timezone.localtime()

    one_minute_ago = now - timedelta(minutes=1)

    # If we haven't gotten a request in the last minute, then don't generate
    return Animation.objects.filter(served_at__gt=one_minute_ago).exists()

def is_present() -> bool:
    return False

def generate_welcome():
    pass

def get_next_animation_time() -> Optional[datetime]:
    now = timezone.localtime()
    last_animation = Animation.objects.latest("start_time")
    next_time = max(last_animation.start_time_local, now)
    # No need to generate if we have animations more than two minutes hence
    if next_time > now + timedelta(minutes=2):
        return

    return Animation.align_time(next_time)


def generate_filler(start_time: datetime):
    os.makedirs(RENDER_DIR, exist_ok=True)
    end_time = start_time + timedelta(minutes=5)
    frames = clock_rays()
    next(frames)
    t = start_time
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
            )
        )
    Animation.objects.bulk_create(animations)


def render(frames, file_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        in_files = [
            convert_frame(temp_path, i, frame) for i, frame in enumerate(frames)
        ]
        frames_arg = " ".join(
            f"-frame {tf} +{FRAME_TIME.total_seconds() * 1000}" for tf in in_files
        )
        cmd = f"webpmux {frames_arg} -loop 1 -bgcolor 255,255,255,255 -o {file_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)


def convert_frame(frame_dir: Path, frame_num: int, frame: Image.Image) -> Path:
    frame_file = frame_dir / f"frame{frame_num:04d}.webp"
    frame.save(frame_file, "WebP", quality=100)
    return frame_file
