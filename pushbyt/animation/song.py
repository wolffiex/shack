from PIL import Image, ImageDraw, ImageFont, ImageChops
from typing import Generator, Optional
from io import BytesIO
import requests
import textwrap
import logging
from unidecode import unidecode


logger = logging.getLogger(__name__)
WIDTH, HEIGHT = 64, 32


def song_info(
    title: str, artist: str, art_url: Optional[str]
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

    title_img = Image.new("RGB", (WIDTH, HEIGHT * 10), color="black")
    draw = ImageDraw.Draw(title_img)
    wrapped_title = textwrap.wrap(unidecode(title), width=10)
    title_height = 1
    for line in wrapped_title:
        draw.text(
            (32, title_height),
            line,
            fill="white",
            anchor="mt",
            align="center",
            font=font,
        )
        title_height += 9

    alpha_step = 1 / 32
    crop_y = title_height // 2 - 16
    title_cropped = title_img.crop((0, crop_y, 64, crop_y + 32))
    for i, top in enumerate(range(32, -1, -1)):
        cropped = art.crop((0, top, 64, top + 32))
        alpha = 1 - alpha_step * i
        faded_art = Image.blend(black_img, cropped, alpha)
        faded_title = Image.blend(title_cropped, black_img, alpha)
        yield ImageChops.screen(faded_art, faded_title)

    artist_img = Image.new("RGB", (WIDTH, HEIGHT * 10), color="black")
    draw = ImageDraw.Draw(artist_img)
    wrapped_artist = textwrap.wrap(unidecode(artist), width=10)
    artist_height = 1
    for line in wrapped_artist:
        draw.text(
            (32, artist_height),
            line,
            fill="white",
            anchor="mt",
            align="center",
            font=font,
        )
        artist_height += 9

    crop_y = artist_height // 2 - 16
    artist_cropped = artist_img.crop((0, crop_y, 64, crop_y + 32))

    for i in range(0, 10):
        yield Image.blend(artist_cropped, title_cropped, 1 - i / 10)

    for i in range(0, 10):
        yield artist_cropped

    for i in range(0, 10):
        yield Image.blend(black_img, artist_cropped, 1 - i / 10)

    yield black_img
