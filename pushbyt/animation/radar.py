from PIL import Image, ImageDraw, ImageFont, ImageChops
from datetime import datetime
from pushbyt.animation import render, FRAME_TIME
import math


WIDTH, HEIGHT = 64, 32
SCALE_FACTOR = 4
SCALED_WIDTH, SCALED_HEIGHT = SCALE_FACTOR * WIDTH, SCALE_FACTOR * HEIGHT


def radar(start_time: datetime):
    t = start_time
    font = ImageFont.truetype("./fonts/DepartureMono/DepartureMono-Regular.ttf", 22)
    hours_px = get_time_pixels(font, "99")
    mins_px = get_time_pixels(font, "99")
    while True:
        yield draw_second_hand(datetime_to_radian(t), hours_px, mins_px)

        t += FRAME_TIME


def get_time_pixels(font, text):
    image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    draw = ImageDraw.Draw(image)
    text_position = (0, 0)
    draw.text(text_position, text, font=font, fill="white")
    # Get the list of white pixel coordinates
    pixels = image.load()
    white_pixels = [
        (x, y) for x in range(WIDTH) for y in range(HEIGHT) if pixels[x, y] != (0, 0, 0)
    ]

    # Calculate the minimum and maximum x and y coordinates
    left = min(x for x, _ in white_pixels)
    right = max(x for x, _ in white_pixels)
    top = min(y for _, y in white_pixels)
    bottom = max(y for _, y in white_pixels)

    # Calculate the offsets to center the pixels
    x_off = (WIDTH // 2 - (right - left)) // 2
    y_off = (HEIGHT - (bottom - top)) // 2

    # Apply the offsets to the pixel coordinates
    return [(x - left + x_off, y - top + y_off) for x, y in white_pixels]


def draw_second_hand(radian, hours_px, mins_px):
    image = Image.new("RGB", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
    center_x, center_y = SCALED_WIDTH // 2, SCALED_HEIGHT // 2
    length = 400

    # Calculate the end point of the line based on the radian value
    end_x = center_x + int(length * math.sin(radian))
    end_y = center_y - int(length * math.cos(radian))

    # Create a new image with a white background
    draw = ImageDraw.Draw(image)

    # Draw the line representing the second hand
    draw.line((center_x, center_y, end_x, end_y), fill="white", width=SCALE_FACTOR)

    draw = ImageDraw.Draw(image)
    finimage = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)
    draw = ImageDraw.Draw(finimage)

    for x, y in hours_px:
        draw.point((x, y), fill="white")
    for x, y in mins_px:
        draw.point((WIDTH // 2 + x, y), fill="white")

    for x in range(32, 33):
        for y in range(11, 13):
            draw.point((x, y), fill="white")
        for y in range(19, 21):
            draw.point((x, y), fill="white")
    return finimage


def datetime_to_radian(t):
    seconds_total = t.second + t.microsecond / 1e6
    return (seconds_total / 60) * 2 * math.pi
