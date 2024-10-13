from django_rich.management import RichCommand
from pushbyt.animation import clock_radar
from pushbyt.animation import FRAME_TIME, render
from pathlib import Path
from itertools import islice
from datetime import datetime


class Command(RichCommand):
    help = "Radar clock rendering tester"

    def handle(self, *args, **options):
        self.console.print("Radar clock", style="bold green")

        self.console.print(self.generate())

    def generate(self):
        t = datetime.now()
        frames = []
        radar = clock_radar()
        next(radar)  # Prime the generator
        
        for _ in range(600):
            frame = radar.send(t)
            frames.append(frame)
            t += FRAME_TIME
        file_path = (Path("render") / "radar-test").with_suffix(".webp")
        render(frames, file_path)
        return file_path.resolve().as_posix()
