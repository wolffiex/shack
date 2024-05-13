from PIL import Image, ImageDraw, ImageFont, ImageChops
from typing import Generator, Optional
from io import BytesIO
import requests
import textwrap
import logging
from unidecode import unidecode


logger = logging.getLogger(__name__)
WIDTH, HEIGHT = 64, 32


def step_color(pixel, amount):
    def step(c):
        return max(0, min(255, c + round(amount)))

    r, g, b = pixel
    return step(r), step(g), step(b)


def song_info(
    title: str, artist: str, art_url: Optional[str]
) -> Generator[Image.Image, str, None]:
    black_img = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
    FONT_WRAP_WIDTH = 12
    if not art_url:
        raise ValueError("Missing art not handled")
    response = requests.get(art_url)
    art_data = response.content
    art = Image.open(BytesIO(art_data))
    for top in range(0, HEIGHT):
        yield art.crop((0, top, WIDTH, top + HEIGHT))

    for _ in range(3):
        yield art.crop((0, HEIGHT, WIDTH, HEIGHT + HEIGHT))

    wrapped_title = textwrap.wrap(unidecode(title), width=FONT_WRAP_WIDTH)
    title_img = text_image(wrapped_title, font)
    _, title_height = title_img.size
    crop_y = title_height // 2 - 16
    title_cropped = title_img.crop((0, crop_y, WIDTH, crop_y + HEIGHT))
    title_pixels = title_cropped.load()
    STEPS = 45
    for i in range(STEPS):
        percentage = i/STEPS
        compressed_height = round(64 - HEIGHT * percentage)
        compressed = art.resize((WIDTH, compressed_height), resample=Image.LANCZOS)
        cropped = compressed.crop(
            (0, compressed_height - HEIGHT, WIDTH, compressed_height)
        )
        img_pixels = cropped.load()
        processed_image = black_img.copy()
        for x in range(WIDTH):
            for y in range(HEIGHT):
                is_in_title = title_pixels[x, y] != (0, 0, 0)
                if is_in_title:
                    step = 200
                else:
                    step = -230
                new_color = step_color(img_pixels[x, y], step * percentage)
                processed_image.putpixel((x, y), new_color)
        yield processed_image

    for i in range(0, 20):
        yield title_cropped

    wrapped_artist = textwrap.wrap(unidecode(artist), width=FONT_WRAP_WIDTH)
    artist_img = text_image(wrapped_artist, font)
    _, artist_height = artist_img.size
    crop_y = artist_height // 2 - 16
    artist_cropped = artist_img.crop((0, crop_y, WIDTH, crop_y + HEIGHT))

    for i in range(0, 20):
        yield Image.blend(artist_cropped, title_cropped, 1 - i / 10)

    for i in range(0, 20):
        yield artist_cropped

    for i in range(0, 10):
        yield Image.blend(black_img, artist_cropped, 1 - i / 10)

    yield black_img


def text_image(lines, font):
    LINE_HEIGHT = 9
    y = 1
    height = y + len(lines) * LINE_HEIGHT
    image = Image.new("RGB", (WIDTH, height), color="black")
    draw = ImageDraw.Draw(image)
    for line in lines:
        # logger.info(f"{line} {font.getsize(line)}")
        draw.text(
            (HEIGHT, y),
            line,
            fill="white",
            anchor="mt",
            align="center",
            font=font,
        )
        y += 9
    return image
