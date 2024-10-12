import math
import random

from PIL import Image, ImageDraw, ImageFont, ImageChops
from datetime import datetime
from pushbyt.animation import render, FRAME_TIME


WIDTH, HEIGHT = 64, 32
SCALE_FACTOR = 4
SCALED_WIDTH, SCALED_HEIGHT = SCALE_FACTOR * WIDTH, SCALE_FACTOR * HEIGHT


def radar(start_time: datetime):
    bg = Background()
    t = start_time
    font = ImageFont.truetype(
        "./fonts/DepartureMono/DepartureMono-Regular.ttf", 22)
    hours_img = get_time_img(font, "99")
    mins_img = get_time_img(font, "99")
    time_image = Image.new("RGBA", (WIDTH, HEIGHT), color="black")
    time_image.paste(hours_img, box=(0, 0))
    time_image.paste(mins_img, box=(32, 0))
    while True:
        yield render_frame(
                datetime_to_radian(t), time_image, bg.render_frame())

        t += FRAME_TIME


def get_time_img(font, text):
    image = Image.new("RGBA", (32, 32), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    text_position = (0, 0)
    # text_width, text_height = draw.textsize(text, font=font)
    # text_position = ((32 - text_width) // 2, (32 - text_height) // 2)
    draw.text(text_position, text, font=font, fill="red")

    # Get the list of white pixel coordinates as a generator
    pixels = image.load()
    non_transparent_pixels = [
        (x, y) for x in range(32) for y in range(32) if pixels[x, y][3] != 0
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
    result = Image.new("RGBA", (32, 32), color=(0, 0, 0, 0))
    result.paste(image, (offset_x, offset_y))

    return result


def second_hand_img(radian) -> Image.Image:
    image = Image.new("L", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
    center_x, center_y = SCALED_WIDTH // 2, SCALED_HEIGHT // 2
    length = 400

    # Calculate the end point of the line based on the radian value
    end_x = center_x + int(length * math.sin(radian))
    end_y = center_y - int(length * math.cos(radian))

    draw = ImageDraw.Draw(image)

    draw.line((center_x, center_y, end_x, end_y),
              fill="white", width=SCALE_FACTOR)

    image = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)

    return image


def transform_ray(ray_image, time_image):
    ray_pixels = ray_image.load()
    time_pixels = time_image.load()
    width, height = ray_image.size

    # Get the list of non-opaque pixel coordinates
    non_opaque_pixels = [
        (x, y) for x in range(width) for y in range(height) if ray_pixels[x, y] != 0
    ]

    # Calculate the distance from the origin for each non-opaque pixel
    distances = [
        math.sqrt((x - width // 2) ** 2 + (y - height // 2) ** 2)
        for x, y in non_opaque_pixels
    ]

    # Sort the non-opaque pixels based on their distances from the origin
    sorted_pixels = [pixel for _, pixel in sorted(
        zip(distances, non_opaque_pixels))]

    # Create a new ray image
    new_ray_image = Image.new("L", ray_image.size, color=0)
    # Set the alpha value for each non-opaque pixel
    step = 0
    for x, y in sorted_pixels:
        if time_pixels[x, y][3] != 0:
            step += ray_pixels[x, y] * 0.2

        c = max(0, ray_pixels[x, y] - int(step))  # Accumulate the step down
        new_ray_image.putpixel((x, y), c)

    return new_ray_image


alpha = Image.new("L", (WIDTH, HEIGHT))


def render_frame(radian, time_image, bg_image):
    global alpha
    ray_image = second_hand_img(radian)
    time_image_copy = time_image.copy()

    # Get the original alpha (transparency) of the time image (the time digits)
    # alpha = Image.eval(alpha, lambda x: int(x * 0.99))
    digits_alpha = time_image.getchannel("A")
    for x in range(WIDTH):
        for y in range(HEIGHT):
            pos = x, y
            ray_a = ray_image.getpixel(pos)
            time_a = alpha.getpixel(pos)
            new_time_a = time_a * 0.99
            if ray_a and digits_alpha.getpixel(pos):
                new_time_a = min(255, time_a + ray_a)
                # print(time_a, ray_a, new_color)
            alpha.putpixel(pos, int(new_time_a))

    # Apply the updated alpha to the time image copy
    time_image_copy.putalpha(alpha)

    ray_image = transform_ray(ray_image, time_image)

    # Create a new blank background
    background = Image.new("RGBA", ray_image.size, color=(0, 0, 0, 0))
    # Use the ray image as a mask for the bg_image
    masked_bg_image = Image.composite(
        bg_image, Image.new("RGB", bg_image.size, color=(0, 0, 0)), ray_image
    )

    # Paste the masked bg_image onto the background
    background.paste(masked_bg_image)

    # Composite the background (with second hand) and the time image
    img = Image.alpha_composite(background, time_image_copy)

    # Optional extra drawing for tick marks, etc.
    draw = ImageDraw.Draw(img)
    for x in range(32, 33):
        for y in range(11, 13):
            draw.point((x, y), fill="white")
        for y in range(19, 21):
            draw.point((x, y), fill="white")

    return img.convert("RGB")


def datetime_to_radian(t):
    seconds_total = t.second + t.microsecond / 1e6
    return (seconds_total / 10) * 2 * math.pi


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
        self.floor_colors = [0.0 if n == drop_color else 125.0
                             for n in range(3)]

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
