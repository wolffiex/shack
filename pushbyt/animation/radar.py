import math
import random
from dataclasses import dataclass
from typing import Tuple, Generator
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont, ImageChops
from datetime import datetime, timedelta
from pushbyt.animation import FRAME_TIME


WIDTH, HEIGHT = 64, 32
SCALE_FACTOR = 4
SCALED_WIDTH, SCALED_HEIGHT = SCALE_FACTOR * WIDTH, SCALE_FACTOR * HEIGHT


def clock_radar(start_time: datetime) -> Generator[Image.Image, datetime, None]:
    font = ImageFont.truetype("./fonts/DepartureMono/DepartureMono-Regular.ttf", 22)
    renderer = Renderer(font, start_time)
    next_frame = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    while True:
        t = yield next_frame
        next_frame = renderer.render_frame(t)


def compose_time_img(font, t: datetime) -> Image.Image:
    hours_text = t.strftime("%l").rjust(2)
    hours_img = get_time_img(font, hours_text)
    mins_img = get_time_img(font, t.strftime("%M"))
    time_image = Image.new("L", (WIDTH, HEIGHT), color="black")
    time_image.paste(hours_img, box=(0, 0))
    time_image.paste(mins_img, box=(32, 0))
    return time_image


def get_time_img(font, text):
    image = Image.new("L", (32, 32), color=0)
    draw = ImageDraw.Draw(image)
    text_position = (0, 0)
    draw.text(text_position, text, font=font, fill="white")

    # Get the list of white pixel coordinates as a generator
    pixels = image.load()
    non_transparent_pixels = [
        (x, y) for x in range(32) for y in range(32) if pixels[x, y] != 0
    ]

    if not non_transparent_pixels:
        return image

    # Calculate the minimum and maximum x and y coordinates
    x_coords, y_coords = zip(*non_transparent_pixels)
    left, right = min(x_coords), max(x_coords)
    top, bottom = min(y_coords), max(y_coords)

    # Calculate the center position
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2

    # Calculate the offset to center the text within the 32x32 square
    offset_x = 16 - center_x
    offset_y = 16 - center_y

    # Create a new 32x32 image and paste the original image with the offset
    result = Image.new("L", (32, 32), color=0)
    result.paste(image, (offset_x, offset_y))

    return result


def get_ray_image(radian) -> Image.Image:
    image = Image.new("L", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
    center_x, center_y = SCALED_WIDTH // 2, SCALED_HEIGHT // 2
    length = 400

    # Calculate the end point of the line based on the radian value
    end_x = center_x + int(length * math.sin(radian))
    end_y = center_y - int(length * math.cos(radian))

    draw = ImageDraw.Draw(image)

    draw.line((center_x, center_y, end_x, end_y), fill="white", width=SCALE_FACTOR)

    image = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)

    return image


def transform_ray(ray_image, time_image):
    ray_pixels = ray_image.load()
    time_pixels = time_image.load()

    # Get the list of non-opaque pixel coordinates
    non_opaque_pixels = [
        (x, y) for x in range(WIDTH) for y in range(HEIGHT) if ray_pixels[x, y] != 0
    ]

    # Calculate the distance from the origin for each non-opaque pixel
    distances = [
        math.sqrt((x - WIDTH // 2) ** 2 + (y - HEIGHT // 2) ** 2)
        for x, y in non_opaque_pixels
    ]

    # Sort the non-opaque pixels based on their distances from the origin
    sorted_pixels = [pixel for _, pixel in sorted(zip(distances, non_opaque_pixels))]

    # Create a new ray image
    new_ray_image = Image.new("L", ray_image.size, color=0)
    # Set the alpha value for each non-opaque pixel
    step = 0
    for x, y in sorted_pixels:
        if time_pixels[x, y] != 0:
            step += ray_pixels[x, y] * 0.1

        c = max(0, ray_pixels[x, y] - int(step))  # Accumulate the step down
        new_ray_image.putpixel((x, y), c)

    return new_ray_image


class SecondHand:
    @dataclass
    class Pixel:
        color = (0, 0, 0)
        alpha = 0
        target_alpha = 0
        v = 0

        def activate(self, bg_color, alpha):
            self.color = bg_color
            if alpha > self.target_alpha:
                self.target_alpha = alpha
                # self.alpha = 0
                self.v = 38

        def step(self) -> Tuple[int, int, int, int]:
            p = (*self.color, self.alpha)
            self.alpha = min(self.target_alpha, max(0, self.alpha + self.v))
            if self.alpha == self.target_alpha:
                self.v  = -3
            return p # type: ignore

    def __init__(self):
        self.fill_img = Image.new("RGB", (WIDTH, HEIGHT), color="black")
        self.black_img = Image.new("RGBA", (WIDTH, HEIGHT), color=(0,0,0,10))
        self.pixels: dict[Tuple[int, int], SecondHand.Pixel] = defaultdict(SecondHand.Pixel)
        self.last_ray_angle = None

    def compose_ray(self, timediff: timedelta, ray_angle, bg_image) -> Image.Image:
        img = Image.new("RGBA", (WIDTH, HEIGHT), color=(0, 0, 0, 0))
        hand_img = get_ray_image(datetime_to_radian(timediff, 60))
        # Check if the ray swept past the second hand
        second_hand_angle = datetime_to_radian(timediff, 60)
        
        is_activate = False
        if self.last_ray_angle is not None:
            a, b = second_hand_angle > self.last_ray_angle, second_hand_angle < ray_angle
            # Handle the case when the ray angle crosses the 0 or 2π radians boundary
            is_activate = (a or b) if ray_angle < self.last_ray_angle else (a and b)
            

        self.last_ray_angle = ray_angle
        if is_activate:
            # The ray swept past the second hand
            self.fill_img = bg_image.copy()
        else:
            self.fill_img.paste(self.black_img, mask=self.black_img)
        

        img.paste(self.fill_img, mask=hand_img)
        return img


class Renderer:
    def __init__(self, font, start_time):
        self.font = font
        self.start_time = start_time
        self.alpha = Image.new("L", (WIDTH, HEIGHT))
        self.time_pixels = TimePixels()
        self.background = Background()
        self.second_hand = SecondHand()

    def render_frame(self, t):
        time_diff = t - self.start_time
        background_img = self.background.render_frame()
        time_image = compose_time_img(self.font, t)
        ray_angle = datetime_to_radian(time_diff, 9)
        ray_image = get_ray_image(ray_angle)

        img = self.time_pixels.zap_with_ray(time_image, ray_image, background_img)
        ray_mask = transform_ray(ray_image, time_image)
        second_hand_img = self.second_hand.compose_ray(time_diff, ray_angle, background_img)
        img.paste(second_hand_img, mask=second_hand_img)
        img.paste(background_img, mask=ray_mask)

        return img


def datetime_to_radian(time_diff: timedelta, steps):
    total_milliseconds = time_diff.total_seconds() * 1000
    angle = (total_milliseconds / (steps * 1000)) * 2 * math.pi
    return angle % (2 * math.pi)


class TimePixels:
    @dataclass
    class Pixel:
        alpha = 0.0
        velocity = 0.0
        color: Tuple[int, int, int] = (0, 0, 0)

        def step(self) -> Tuple[int, int, int]:
            alpha = max(0.0, self.alpha + self.velocity)
            if alpha > 1.0:
                alpha = 1.0
                self.velocity = -0.01
            self.alpha = alpha
            return tuple(int(c * self.alpha) for c in self.color)

    def __init__(self):
        d = defaultdict(TimePixels.Pixel)
        self.pixels: dict[Tuple[int, int], TimePixels.Pixel] = d

    def zap_with_ray(self, time_image, ray_image, bg_image):
        ray_pixels = ray_image.load()
        time_image_pixels = time_image.load()
        bg_pixels = bg_image.load()
        for x in range(WIDTH):
            for y in range(HEIGHT):
                a = ray_pixels[x, y]
                if a > 15 and time_image_pixels[x, y]:
                    pxl = self.pixels[x, y]
                    pxl.velocity = 0.18
                    pxl.color = bg_pixels[x, y]
        img = Image.new("RGB", (WIDTH, HEIGHT), color="black")
        for point, px in self.pixels.items():
            img.putpixel(point, px.step())
        return img


class Background:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.center_x = WIDTH // 2
        self.center_y = HEIGHT // 2
        self.center_color = (155, 155, 175)
        self.edge_color = (175, 135, 155)
        self.velocity = [0.5, -3.0, 4.0]
        drop_color = random.randint(0, 2)
        self.floor_colors = [0.0 if n == drop_color else 125.0 for n in range(3)]

    def shift_colors(self):
        for i in range(3):
            c = self.center_color[i]
            floor = self.floor_colors[i]
            v = self.velocity[i]
            r = 5 * random.random()
            if c <= floor and v < 0:
                self.velocity[i] = r
            elif c >= 255.0 and v > 0:
                self.velocity[i] = -r

        def apply_velocity(color):
            return tuple(
                max(floor, min(c + v, 255.0))
                for floor, c, v in zip(self.floor_colors, color, self.velocity)
            )

        # print(self.center_color, self.velocity)
        self.center_color = apply_velocity(self.center_color)
        self.edge_color = apply_velocity(self.edge_color)

    def render_frame(self):
        self.shift_colors()
        # Create a new PIL image
        image = Image.new("RGB", (self.width, self.height))
        pixels = image.load()
        max_distance = math.sqrt(self.center_x**2 + self.center_y**2)

        for y in range(self.height):
            for x in range(self.width):
                distance = math.sqrt(
                    (x - self.center_x) ** 2 + (y - self.center_y) ** 2
                )
                normalized_distance = distance / max_distance

                # Interpolate between center color and edge color based on the normalized distance
                color = tuple(
                    int(c + (e - c) * normalized_distance)
                    for c, e in zip(self.center_color, self.edge_color)
                )

                # Set the pixel color in the PIL image
                pixels[x, y] = color

        return image
