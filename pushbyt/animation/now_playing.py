from PIL import Image, ImageDraw, ImageFont, ImageChops
from typing import Generator, Optional
from io import BytesIO
import requests
import textwrap
import logging
from unidecode import unidecode


logger = logging.getLogger(__name__)
WIDTH, HEIGHT = 64, 32


def generate(
    track: str, artist: str, art_url: Optional[str]
) -> Generator[Image.Image, str, None]:
    black_img = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
    if not art_url:
        raise ValueError("Missing art not handled")
    response = requests.get(art_url)
    art_data = response.content
    art = Image.open(BytesIO(art_data))

    for top in range(0, 32):
        yield art.crop((0, top, 64, top + 32))

    track_text = Image.new("RGB", (WIDTH, HEIGHT * 10), color="black")
    alpha_step = 1/32
    for i, top in enumerate(range(32, 64)):
        cropped = art.crop((0, top, 64, 64))
        resized = black_img.copy()
        resized.paste(cropped)
        faded_art = Image.blend(black_img, resized, 1-alpha_step*i)
        yield faded_art


    artist_text = Image.new("RGB", (WIDTH, HEIGHT * 10), color="black")
    draw = ImageDraw.Draw(artist_text)
    wrapped_artist = textwrap.wrap(unidecode(artist), width=10)
    y = 1
    for line in wrapped_artist:
        draw.text(
            (32, y), line, fill="white", anchor="mt", align="center", font=font
        )
        y += 9

    for _ in range(25):
        yield artist_text.crop((0, 0, 64, 32))

