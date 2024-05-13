from PIL import Image, ImageDraw, ImageFont, ImageChops
from typing import Generator, Optional
import logging
from datetime import timedelta


logger = logging.getLogger(__name__)
WIDTH, HEIGHT = 64, 32


def timer(delta: timedelta) -> Generator[Image.Image, str, None]:
    # font = ImageFont.truetype("./fonts/m12_match_biker/m12.TTF", 16)
    # font = ImageFont.truetype("fonts/perfect_dos_vga_437/Perfect DOS VGA 437.ttf", 16)
    # font = ImageFont.truetype("fonts/upheaval/upheavtt.ttf", 20)
    font = ImageFont.truetype("fonts/tall-pixel-8x3/tall-pixel-8x3.ttf", 9)
    minutes, seconds = divmod(delta.seconds, 60)
    yield text_image(f"{minutes:02d}{seconds:02d}", font)


DIGIT_WIDTH = 14
DIGIT_HEIGHT = 26


def digit_image(c, font):
    # image = Image.new("RGB", (DIGIT_WIDTH, DIGIT_HEIGHT), "black")
    image = Image.new("RGB", (DIGIT_WIDTH, DIGIT_HEIGHT), (50,50,50))
    draw = ImageDraw.Draw(image)
    draw.text(
        # (DIGIT_WIDTH // 2, 0), #DIGIT_HEIGHT // 2),
        (0, 0), #DIGIT_HEIGHT // 2),
        c,
        fill="white",
        # anchor="lt",
        font=font,
    )
    return image


def text_image(digits, font):
    y = 16 - DIGIT_HEIGHT // 2
    print(y)
    y = 2
    x = 2
    imgs = [digit_image(c, font) for c in [*digits]]
    image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    image = Image.new("RGB", (WIDTH, HEIGHT), color="red")
    for i, img in enumerate(imgs):
        is_left = i < 2
        n = [-2, -1, 0, 1][i]
        adjust = -2 if is_left else 2
        # x = 32 + adjust + n * DIGIT_WIDTH
        image.paste(img, (x, y))
        x +=10

    draw = ImageDraw.Draw(image)
    coords = [(30, 13, 32, 15), (30, 17, 32, 19)]
    for coord in coords:
        draw.rectangle(coord, fill="white")

    return image
