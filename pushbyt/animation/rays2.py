from PIL import Image, ImageDraw, ImageFont, ImageChops
import math
import random
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache
from typing import Generator


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def to_tuple(self):
        return (self.x, self.y)


WIDTH, HEIGHT = 64, 32
SCALE_FACTOR = 4
CENTER = Point(SCALE_FACTOR * WIDTH / 2, SCALE_FACTOR * HEIGHT / 2)
SCALED_WIDTH, SCALED_HEIGHT = SCALE_FACTOR * WIDTH, SCALE_FACTOR * HEIGHT


FONT_PATH = "./fonts/pixel12x10/Pixel12x10-v1.1.0.ttf"

# Colon drawn by hand so its upper block can stay unlit and serve as ray origin.
DOT_SIZE = 2
UPPER_DOT_OFFSET = 3
LOWER_DOT_OFFSET = 9
COLON_GAP = 2


@lru_cache(maxsize=8)
def get_time_pixels(time_str: str) -> tuple[tuple[tuple[int, int], ...], Point]:
    """Lit pixels and ray origin, laid out around a colon pinned to center.

    Centering the whole string would slide the colon ~8px on single-digit
    hours, dragging the origin with it. The upper block is left unlit: it is
    the origin, drawn by the rays passing through it.
    """
    image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    font = get_font()
    draw = ImageDraw.Draw(image)

    hours, _, minutes = time_str.partition(":")
    dot_left = (WIDTH - DOT_SIZE) // 2
    dot_right = dot_left + DOT_SIZE - 1

    bbox = draw.textbbox((0, 0), time_str, font=font)
    top = (HEIGHT - (bbox[3] - bbox[1])) // 2
    dot_top = top + LOWER_DOT_OFFSET

    draw.text(
        (dot_left - COLON_GAP - 1 - ink_bounds(hours)[1], top),
        hours,
        font=font,
        fill="white",
    )
    draw.text(
        (dot_right + 1 + COLON_GAP - ink_bounds(minutes)[0], top),
        minutes,
        font=font,
        fill="white",
    )
    draw.rectangle([dot_left, dot_top, dot_right, dot_top + DOT_SIZE - 1], fill="white")

    pixels = image.load()
    lit = tuple(
        (x, y) for x in range(WIDTH) for y in range(HEIGHT) if pixels[x, y] != (0, 0, 0)
    )
    return lit, Point(
        SCALE_FACTOR * (dot_left + DOT_SIZE / 2),
        SCALE_FACTOR * (top + UPPER_DOT_OFFSET + DOT_SIZE / 2),
    )


@lru_cache(maxsize=1)
def get_font() -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, 16)


@lru_cache(maxsize=None)
def ink_bounds(text: str) -> tuple[int, int]:
    """Inclusive x range of a string's ink. font.getbbox() would give the
    advance box, bearings included; the mask bbox is the ink."""
    bbox = get_font().getmask(text).getbbox()
    return (bbox[0], bbox[2] - 1) if bbox else (0, 0)


@dataclass
class Ray:
    angle: float
    origin: Point = CENTER
    _start: float = 0.0
    _end: float = 0.01
    color = (255, 150, 150)

    @classmethod
    def new(cls, origin: Point = CENTER):
        angle = random.uniform(0, 2 * math.pi)
        return Ray(angle, origin)

    def to_line(self):
        return [self.start.to_tuple(), self.end.to_tuple()]

    def is_in_bounds(self):
        return (
            self.start.x >= 0
            and self.start.x < SCALED_WIDTH
            and self.start.y >= 0
            and self.start.y < SCALED_HEIGHT
        )

    def animate(self):
        self._start += 0.04
        self._end += 0.06
        self.color = combine_colors(self.color, (-10, 0, 10))
        assert len(self.color) == 3

    @property
    def start(self):
        return self._to_point(self._start)

    @property
    def end(self):
        return self._to_point(self._end)

    def _to_point(self, percent):
        x = self.origin.x + SCALED_WIDTH * percent * math.cos(self.angle)
        y = self.origin.y + SCALED_WIDTH * percent * math.sin(self.angle)
        return Point(x, y)


def clock_rays() -> Generator[Image.Image, datetime, None]:
    rays = []
    black_image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    time_image = black_image.copy()
    time_str = None
    next_frame = black_image
    while True:
        t = yield next_frame
        time_str = t.strftime("%-I:%M")
        all_time_pixels, ray_origin = get_time_pixels(time_str)
        for _ in range(random.randint(1, 4)):
            rays.append(Ray.new(ray_origin))

        image = Image.new("RGB", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
        draw = ImageDraw.Draw(image)
        for ray in rays:
            draw.line(ray.to_line(), fill=ray.color, width=SCALE_FACTOR)
            ray.animate()

        image_lo = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)
        image_pixels = image_lo.load()
        time_pixels = time_image.load()
        for x, y in all_time_pixels:
            time_image.putpixel(
                (x, y), combine_colors(image_pixels[x, y], time_pixels[x, y])
            )

        next_frame = ImageChops.screen(image_lo, time_image)
        # Phosphor decay: a glyph stays lit ~2.5s after a ray crosses it.
        time_image = Image.blend(time_image, black_image, alpha=0.04)
        rays = [ray for ray in rays if ray.is_in_bounds()]


def combine_colors(aa, bb):
    color = tuple(max(0, min(255, a + b)) for a, b in zip(aa, bb))
    assert len(color) == 3
    return color
