from django.http import HttpResponse
from pushbyt.animation.rays import clock_rays
import logging
from datetime import datetime
import asyncio
import tempfile
import aiofiles
import aiofiles.os
import subprocess


logger = logging.getLogger(__name__)


async def get_webp(_):
    frames = clock_rays(get_local_time_str())
    webp_bytes = await webpmux(frames)

    response = HttpResponse(webp_bytes, content_type="image/webp")

    return response



async def convert_frame(frame):
    async with aiofiles.tempfile.NamedTemporaryFile(
        suffix=".webp", delete=False
    ) as temp_file:
        frame_name = temp_file.name
    frame.save(frame_name, "WebP", quality=100)
    return frame_name


async def remove_temp_file(temp_file):
    await aiofiles.os.unlink(temp_file)


FRAME_TIME = 100


async def webpmux(frames):
    assert len(frames) <= 150
    convert_tasks = [asyncio.create_task(convert_frame(frame)) for frame in frames]
    in_files = await asyncio.gather(*convert_tasks)
    with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as temp_file:
        out_file = temp_file.name
    frames_arg = " ".join(f"-frame {tf} +{FRAME_TIME}" for tf in in_files)
    cmd = f"webpmux {frames_arg} -loop 1 -bgcolor 255,255,255,255 -o {out_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    with open(out_file, "rb") as file:
        file_bytes = file.read()

    removal_tasks = [
        asyncio.create_task(remove_temp_file(temp_file))
        for temp_file in in_files + [out_file]
    ]
    await asyncio.gather(*removal_tasks)

    return file_bytes
