from PIL import Image, ImageDraw, ImageFont, ImageChops
import math
import random
from dataclasses import dataclass
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


def get_time_pixels(time_str):
    image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    # font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
    # font = ImageFont.truetype("./fonts/freecam/freecam v2.ttf", 16)
    font = ImageFont.truetype("./fonts/pixel12x10/Pixel12x10-v1.1.0.ttf", 16)
    draw = ImageDraw.Draw(image)
    text_position = (0, 0)
    bbox = draw.textbbox(text_position, time_str, font=font)
    left, top, right, bottom = bbox
    text_width = right - left
    text_height = bottom - top

    # Calculate the new coordinates to center the bounding box
    new_left = (WIDTH - text_width) // 2
    new_top = (HEIGHT - text_height) // 2
    draw.text((new_left, new_top), time_str, font=font, fill="white")
    pixels = image.load()
    return [
        (x, y) for x in range(WIDTH) for y in range(HEIGHT) if pixels[x, y] != (0, 0, 0)
    ]


frames = [Image.new("RGB", (WIDTH, HEIGHT), color="black")]


@dataclass
class Ray:
    angle: float
    _start: float = 0.0
    _end: float = 0.01
    color = (255, 150, 150)

    @classmethod
    def new(cls):
        angle = random.uniform(0, 2 * math.pi)
        return Ray(angle)

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
        x = CENTER.x + SCALED_WIDTH * percent * math.cos(self.angle)
        y = CENTER.y + SCALED_WIDTH * percent * math.sin(self.angle)
        return Point(x, y)


def clock_rays() -> Generator[Image.Image, str, None]:
    rays = []
    black_image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    time_image = black_image.copy()
    time_str = None
    next_frame = black_image
    while True:
        time_str = yield next_frame
        all_time_pixels = get_time_pixels(time_str)
        for _ in range(random.randint(1, 4)):
            rays.append(Ray.new())

        image = Image.new("RGB", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
        draw = ImageDraw.Draw(image)
        for ray in rays:
            draw.line(ray.to_line(), fill=ray.color, width=SCALE_FACTOR)
            ray.animate()

        # Downsample the high-resolution image to the desired size
        image_lo = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)
        image_pixels = image_lo.load()
        time_pixels = time_image.load()
        for x, y in all_time_pixels:
            time_image.putpixel(
                (x, y), combine_colors(image_pixels[x, y], time_pixels[x, y])
            )

        next_frame = ImageChops.screen(image_lo, time_image)
        # fade time image
        time_image = Image.blend(time_image, black_image, alpha=0.04)
        rays = [ray for ray in rays if ray.is_in_bounds()]


def combine_colors(aa, bb):
    color = tuple(max(0, min(255, a + b)) for a, b in zip(aa, bb))
    assert len(color) == 3
    return color
