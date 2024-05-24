from django_rich.management import RichCommand
from pushbyt.animation import radar
from pushbyt.animation import render
from pathlib import Path
from itertools import islice
from datetime import datetime


class Command(RichCommand):
    help = "Radar clock rendering tester"

    def handle(self, *args, **options):
        self.console.print("Radar clock", style="bold green")

        self.console.print(self.generate())

    def generate(self):
        now = datetime.now()
        frames = islice(radar(now), 0, 600)
        file_path = (Path("render") / "radar-test").with_suffix(
            ".webp"
        )
        render(frames, file_path)
        return file_path.resolve().as_posix()
