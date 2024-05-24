from PIL import Image, ImageDraw, ImageFont, ImageChops
from datetime import datetime
from pushbyt.animation import render, FRAME_TIME
import math


WIDTH, HEIGHT = 64, 32
SCALE_FACTOR = 4
SCALED_WIDTH, SCALED_HEIGHT = SCALE_FACTOR * WIDTH, SCALE_FACTOR * HEIGHT


def radar(start_time: datetime):
    t = start_time
    while True:
        yield draw_second_hand(datetime_to_radian(t))

        t += FRAME_TIME


def draw_second_hand(radian):
    image = Image.new("RGB", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
    center_x, center_y = SCALED_WIDTH // 2, SCALED_HEIGHT // 2
    length = 400

    # Calculate the end point of the line based on the radian value
    end_x = center_x + int(length * math.sin(radian))
    end_y = center_y - int(length * math.cos(radian))

    # Create a new image with a white background
    draw = ImageDraw.Draw(image)

    # Draw the line representing the second hand
    draw.line((center_x, center_y, end_x, end_y),
              fill="red", width=SCALE_FACTOR)

    return image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)


def datetime_to_radian(t):
    seconds_total = t.second + t.microsecond / 1e6
    return (seconds_total / 60) * 2 * math.pi
