from django_rich.management import RichCommand
from rich.table import Table
from pushbyt.animation import render
from pushbyt.animation.timer import timer
from pathlib import Path
from datetime import timedelta


class Command(RichCommand):
    help = "Timer rendering tester"

    def handle(self, *args, **options):
        self.console.print("Rendering timer", style="bold green")

        test_1 = "one", timedelta(minutes=19, seconds=54)
        test_2 = "two", timedelta(minutes=69, seconds=59)

        table = Table(title="Test animations")
        table.add_column("Time delta", style="cyan")
        table.add_column("Path", style="magenta")
        table.add_row(*self.generate(test_1))
        table.add_row(*self.generate(test_2))

        self.console.print(table)

    def generate(self, info):
        name, delta = info
        frames = [ *timer(delta) ]
        file_path = (Path("render") / f"timer-{name}").with_suffix(
            ".webp"
        )
        render(frames, file_path)
        return name, file_path.resolve().as_posix()


