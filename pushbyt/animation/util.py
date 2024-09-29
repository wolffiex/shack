import tempfile
import subprocess
import logging
import os
from PIL import Image
from pathlib import Path
from datetime import timedelta

logger = logging.getLogger(__name__)

FRAME_TIME = timedelta(milliseconds=100)
SWAP_PALETTE = bool(os.getenv("PUSHBYT_PALETTE_SWAP"))


def render(frames, file_path) -> bool:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        in_files = [
            convert_frame(temp_path, i, frame) for i, frame in enumerate(frames)
        ]
        if not in_files:
            return False
        frames_arg = " ".join(
            f"-frame {tf} +{FRAME_TIME.total_seconds() * 1000}" for tf in in_files
        )
        cmd = f"webpmux {
            frames_arg} -loop 1 -bgcolor 255,255,255,255 -o {file_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return True


def convert_frame(frame_dir: Path, frame_num: int, frame: Image.Image) -> Path:
    frame_file = frame_dir / f"frame{frame_num:04d}.webp"
    if SWAP_PALETTE:
        frame = swap_palette(frame)
    try:
        frame.save(frame_file, "WebP", quality=100)
        return frame_file
    except Exception as e:
        logging.error(f"Error encoding frame {frame_num}: {e}")
        logging.error(f"Frame size: {frame.size}, Frame mode: {frame.mode}")
        raise


def swap_palette(frame):
    r, g, b = frame.convert("RGB").split()
    return Image.merge("RGB", (b, r, g))
