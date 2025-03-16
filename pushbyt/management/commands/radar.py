from django_rich.management import RichCommand
from pushbyt.animation import clock_radar
from pushbyt.animation import FRAME_TIME, render
from pathlib import Path
from itertools import islice
from datetime import datetime, timedelta


class Command(RichCommand):
    help = "Radar clock rendering tester"

    def handle(self, *args, **options):
        self.console.print("Radar clock", style="bold green")

        self.console.print(self.generate())

    def generate(self):
        # Round to the nearest second to ensure synchronization
        now = datetime.now().replace(microsecond=0)
        # Calculate a start_time that aligns with the 15-second interval
        current_second = now.second
        second_offset = current_second % 15
        start_time = now - timedelta(seconds=second_offset)

        frames = []
        radar = clock_radar(start_time)
        next(radar)  # Prime the generator

        # Generate 15 seconds of animation (150 frames at 10 FPS)
        t = now.replace(microsecond=0)
        for _ in range(150):
            frame = radar.send(t)
            frames.append(frame)
            t += FRAME_TIME
        file_path = (Path("render") / "radar-test").with_suffix(".webp")
        render(frames, file_path)
        return file_path.resolve().as_posix()
