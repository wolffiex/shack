from PIL import Image, ImageDraw, ImageFont, ImageChops
from typing import Generator, Optional
import logging
from datetime import timedelta
from pushbyt.animation.util import FRAME_TIME


logger = logging.getLogger(__name__)
WIDTH, HEIGHT = 64, 32

DIGIT_WIDTH = 12
DIGIT_HEIGHT = 10


def timer(delta: timedelta) -> Generator[Image.Image, str, None]:
    font = ImageFont.truetype("fonts/upheaval/upheavtt.ttf", 20)
    td = delta
    while td > -timedelta(seconds=10):
        sub_second = td.microseconds // FRAME_TIME.microseconds
        if td > timedelta(seconds=0):
            current_digits = to_min_sec(td)
            next_digits = to_min_sec(td - timedelta(seconds=1))
            digit_images = [
                combine_digits(font, sub_second, c, n)
                for c, n in zip(current_digits, next_digits)
            ]
            yield text_image(digit_images, sub_second)
        else:
            color = "red" if sub_second % 2 == 1 else "black"
            yield Image.new("RGB", (WIDTH, HEIGHT), color)
        td -= FRAME_TIME


def combine_digits(font, sub_second, old_digit, new_digit):
    old_img = digit_image(old_digit, font)
    if sub_second > 7 or old_digit == new_digit:
        return old_img

    step = 7 - sub_second

    new_img = digit_image(new_digit, font)
    oldp = old_img.load()
    newp = new_img.load()
    mid = DIGIT_HEIGHT // 2
    top = mid - step
    bot = mid + step
    compo_img = Image.new("RGB", (DIGIT_WIDTH, DIGIT_HEIGHT), "black")
    for x in range(DIGIT_WIDTH):
        for y in range(DIGIT_HEIGHT):
            if y == top or y == bot:
                inold = oldp[x, y] != (0, 0, 0)
                innew = newp[x, y] != (0, 0, 0)
                # this is frontier
                if inold and innew:
                    compo_img.putpixel((x, y), (255, 255, 255))
                elif inold and not innew:
                    compo_img.putpixel((x, y), (255, 0, 0))
                elif innew and not inold:
                    compo_img.putpixel((x, y), (0, 255, 0))
                # else not in either
            elif y < top or y > bot:
                # show old
                compo_img.putpixel((x, y), oldp[x, y])
            else:
                # show new
                compo_img.putpixel((x, y), newp[x, y])
    return compo_img


def to_min_sec(td):
    ts = int(td.total_seconds())
    minutes, seconds = divmod(ts, 60)
    return [*f"{minutes:02d}{seconds:02d}"]


def digit_image(c, font):
    image = Image.new("RGB", (DIGIT_WIDTH, DIGIT_HEIGHT), "black")
    draw = ImageDraw.Draw(image)
    draw.text(
        (DIGIT_WIDTH // 2, 0),  # DIGIT_HEIGHT // 2),
        # (0, 0), #DIGIT_HEIGHT // 2),
        c,
        fill="white",
        anchor="mt",
        font=font,
    )
    return image


def text_image(digit_images, sub_second):
    y = 16 - DIGIT_HEIGHT // 2
    image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    for i, img in enumerate(digit_images):
        is_left = i < 2
        n = [-2, -1, 0, 1][i]
        adjust = -3 if is_left else 3
        x = 32 + adjust + n * DIGIT_WIDTH
        image.paste(img, (x, y))
        x += 12

    draw = ImageDraw.Draw(image)
    coords = [(30, 13, 32, 14), (30, 17, 32, 18)]
    c = round(255 - abs(sub_second - 5) / 5 * 100)
    fill_color = (c, c, c)
    for coord in coords:
        draw.rectangle(coord, fill=fill_color)

    return image
