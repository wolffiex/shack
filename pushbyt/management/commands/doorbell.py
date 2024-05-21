from django_rich.management import RichCommand
from pushbyt.animation import render
from pathlib import Path
from PIL import Image
from pushbyt.views.doorbell import DOORBELL_PATH


WIDTH, HEIGHT = 64, 32


class Command(RichCommand):
    help = "Generate doorbell animation"

    def handle(self, *args, **options):
        self.console.print("Rendering doorbell animation", style="bold green")
        black_img = Image.new("RGB", (WIDTH, HEIGHT), "black")

        door, bell, bellhop = [Image.open(
            f"static/{f}.png") for f in ["door", "bell", "bellhop"]]

        file_path = (Path("render") / "doorbell").with_suffix(".webp")
        fp_string = file_path.resolve().as_posix()
        frames = []
        frame_base = black_img.copy()
        frame_base.paste(bell, (0, 0))
        frame_base.paste(bellhop, (32, 0))
        for i in range(150):
            frame = frame_base.copy()
            frame.paste(door, (i % 64 - door.width, 1))
            frames.append(frame)
        render(frames, fp_string)
        self.console.print('Filepath:')
        self.console.print(fp_string, style="bold green")
