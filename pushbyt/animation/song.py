from PIL import Image, ImageDraw, ImageFont, ImageChops
from collections import defaultdict
from typing import Generator, Optional
from io import BytesIO
import requests
import textwrap
import logging
from unidecode import unidecode


logger = logging.getLogger(__name__)
WIDTH, HEIGHT = 64, 32
BORDER_HEIGHT = 3
ART_HEIGHT = 64


def step_color(pixel, amount):
    def step(c):
        return max(0, min(255, c + round(amount)))

    r, g, b = pixel
    return step(r), step(g), step(b)


def song_info(
    title: str, artist: str, art_url: Optional[str]
) -> Generator[Image.Image, str, None]:
    font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
    if not art_url:
        raise ValueError("Missing art not handled")
    art_scroll = gen_album_art(art_url)
    for _ in range(25):
        yield next(art_scroll)
    yield from show_text(title, font, art_scroll)
    yield from show_text(artist, font, art_scroll, True)


def show_text(text, font, art_scroll, reverse_fade=False):
    FONT_WRAP_WIDTH = 12
    black_img = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    wrapped_title = textwrap.wrap(unidecode(text), width=FONT_WRAP_WIDTH)
    title_img = text_image(wrapped_title, font)
    _, title_height = title_img.size
    needs_scroll = title_height > HEIGHT

    TEXT_FRAMES = 50
    for i in range(TEXT_FRAMES):
        fade = i/TEXT_FRAMES
        if reverse_fade:
            fade = 1-fade
        if needs_scroll:
            title_overhang = TEXT_FRAMES - (title_height - HEIGHT)
            title_y = min(title_height - HEIGHT, max(0, i-title_overhang//2))
        else:
            title_y = title_height // 2 - 16
        title_cropped = title_img.crop((0, title_y, WIDTH, title_y + HEIGHT))
        title_pixels = title_cropped.load()
        art_img = next(art_scroll)
        art_pixels = art_img.load()
        processed_image = black_img.copy()
        for x in range(WIDTH):
            for y in range(HEIGHT):
                is_in_title = title_pixels[x, y] != (0, 0, 0)
                if is_in_title:
                    step = 150
                else:
                    step = -180
                new_color = step_color(art_pixels[x, y], step * fade)
                processed_image.putpixel((x, y), new_color)
        yield processed_image

    # for top in range(0, HEIGHT):
    #     yield art.crop((0, top, WIDTH, top + HEIGHT))

    # for _ in range(3):
    #     yield art.crop((0, HEIGHT, WIDTH, HEIGHT + HEIGHT))

    # wrapped_title = textwrap.wrap(unidecode(title), width=FONT_WRAP_WIDTH)
    # title_img = text_image(wrapped_title, font)
    # _, title_height = title_img.size
    # crop_y = title_height // 2 - 16
    # title_cropped = title_img.crop((0, crop_y, WIDTH, crop_y + HEIGHT))
    # title_pixels = title_cropped.load()
    # STEPS = 45
    # for i in range(STEPS):
    #     percentage = i/STEPS
    #     compressed_height = round(64 - HEIGHT * percentage)
    #     compressed = art.resize(
    #         (WIDTH, compressed_height), resample=Image.LANCZOS)
    #     cropped = compressed.crop(
    #         (0, compressed_height - HEIGHT, WIDTH, compressed_height)
    #     )
    #     img_pixels = cropped.load()
    #     processed_image = black_img.copy()
    #     for x in range(WIDTH):
    #         for y in range(HEIGHT):
    #             is_in_title = title_pixels[x, y] != (0, 0, 0)
    #             if is_in_title:
    #                 step = 200
    #             else:
    #                 step = -230
    #             new_color = step_color(img_pixels[x, y], step * percentage)
    #             processed_image.putpixel((x, y), new_color)
    #     yield processed_image

    # for i in range(0, 20):
    #     yield title_cropped

    # wrapped_artist = textwrap.wrap(unidecode(artist), width=FONT_WRAP_WIDTH)
    # artist_img = text_image(wrapped_artist, font)
    # _, artist_height = artist_img.size
    # crop_y = artist_height // 2 - 16
    # artist_cropped = artist_img.crop((0, crop_y, WIDTH, crop_y + HEIGHT))

    # for i in range(0, 20):
    #     yield Image.blend(artist_cropped, title_cropped, 1 - i / 10)

    # for i in range(0, 20):
    #     yield artist_cropped

    # for i in range(0, 10):
    #     yield Image.blend(black_img, artist_cropped, 1 - i / 10)

    # yield black_img


def gen_album_art(art_url):
    response = requests.get(art_url)
    art_data = response.content
    art = Image.open(BytesIO(art_data))
    tiled_img = Image.new("RGB", (WIDTH, ART_HEIGHT*2 + BORDER_HEIGHT),
                          color="black")
    tiled_img.paste(art, (0, 0))
    tiled_img.paste(art, (0, ART_HEIGHT + BORDER_HEIGHT))
    dominant_color = get_dominant_color(art)
    border = gen_art_border(dominant_color)
    while True:
        for top in range(0, ART_HEIGHT + 3):
            frame = tiled_img.copy()
            border_frame = next(border)
            frame.paste(border_frame, (0, 64))
            yield frame.crop((0, top, WIDTH, top + HEIGHT))


def gen_art_border(color):
    diamonds = Image.new('RGB', (68, 3), color='black')
    draw = ImageDraw.Draw(diamonds)
    reverse_dir = False

    for x in range(0, 68, 4):
        draw.polygon([(x, 1), (x+1, 0), (x+2, 1), (x+1, 2)], fill=color)

    while True:
        reverse_dir = not reverse_dir
        for _ in range(4):
            for x in range(4):
                if reverse_dir:
                    x = 4 - x
                yield diamonds.crop((x, 0, 64+x, 3))


def get_dominant_color(image):
    pixels = image.load()
    width, height = image.size

    color_count = defaultdict(int)

    for x in range(width):
        for y in range(height):
            color = pixels[x, y]
            quantized_color = tuple(int(channel / 10) for channel in color)
            if sum(quantized_color) > 8:
                color_count[quantized_color] += 1

    if color_count:
        dominant_color = max(color_count, key=color_count.get)
        return tuple(channel * 10 for channel in dominant_color)
    else:
        return (255, 255, 255)


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
