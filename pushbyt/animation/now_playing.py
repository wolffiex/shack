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
    font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
    if not art_url:
        raise ValueError("Missing art not handled")
    response = requests.get(art_url)
    art_data = response.content
    art = Image.open(BytesIO(art_data))

    for top in range(0, 32):
        yield art.crop((0, top, 64, top + 32))

    rendered_text = Image.new("RGB", (WIDTH, HEIGHT * 10), color="black")
    draw = ImageDraw.Draw(rendered_text)
    wrapped_artist = textwrap.wrap(unidecode(artist), width=10)
    y = 1
    for line in wrapped_artist:
        draw.text(
            (32, y), line, fill="white", anchor="mt", align="center", font=font
        )
        y += 9

    for _ in range(25):
        yield rendered_text.crop((0, 0, 64, 32))

    # alpha = 0
    # alpha_step = 0.05
