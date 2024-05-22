from django_rich.management import RichCommand
from pushbyt.animation.song import song_info
from rich.table import Table
from pushbyt.spotify import now_playing
from pushbyt.animation import render
from pathlib import Path


class Command(RichCommand):
    help = "Song rendering tester"

    def handle(self, *args, **options):
        self.console.print("Rendering songs", style="bold green")

        track_1 = {
            "title": "Too Much Brandy",
            "artist": "The Streets",
            "art": "https://i.scdn.co/image/ab67616d00004851b35c6da432ec9a1a2f2df1af",
            "id": 1,
        }

        track_2 = {
            "id": 2,
            "title": "420",
            "artist": "STS, RJD2",
            "art": "https://i.scdn.co/image/ab67616d0000485127c7bcadf68b3feec0829b1b",
        }

        track_3 = {
            "id": "3",
            "title": "Modern Girl",
            "artist": "Bleachers",
            "art": "https://i.scdn.co/image/ab67616d000048518acf3fbdae4c4a93992b59a7",
        }
        track_4 = {
            "id": "4",
            "title": "Heart Of Glass Reart for Fass Bing Too Tass",
            "artist": "Blondie",
            "art": "https://i.scdn.co/image/ab67616d00004851ace2bedb8e6cfa04207d5c0f",
        }

        table = Table(title="Test animations")
        table.add_column("Title", style="cyan")
        table.add_column("Path 2", style="magenta")
        table.add_row(*self.generate(track_1))
        table.add_row(*self.generate(track_2))
        table.add_row(*self.generate(track_3))
        table.add_row(*self.generate(track_4))

        self.console.print(table)

    def generate(self, track_info):
        frames = [
            *song_info(track_info["title"], track_info["artist"], track_info["art"])
        ]
        file_path = (Path("render") / f"spotify-{track_info["id"]}").with_suffix(
            ".webp"
        )
        render(frames, file_path)
        return track_info["title"], file_path.resolve().as_posix()
