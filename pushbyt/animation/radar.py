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
    hours_img = get_time_img(font, "99")
    mins_img = get_time_img(font, "99")
    while True:
        yield render_frame(datetime_to_radian(t), hours_img, mins_img)

        t += FRAME_TIME


def get_time_img(font, text):
    image = Image.new("RGBA", (32, 32), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    text_position = (0, 0)
    draw.text(text_position, text, font=font, fill="gray")

    # Get the list of white pixel coordinates as a generator
    pixels = image.load()
    white_pixels = (
        (x, y) for x in range(32) for y in range(32) if pixels[x, y] != (0, 0, 0)
    )

    if not any(white_pixels):
        return image

    # Calculate the minimum and maximum x and y coordinates
    x_coords, y_coords = zip(*white_pixels)
    left, right = min(x_coords), max(x_coords)
    top, bottom = min(y_coords), max(y_coords)

    # Crop the image based on the bounding box
    cropped_image = image.crop((left, top, right + 1, bottom + 1))

    # Create a new 32x32 image and paste the cropped image in the center
    result = Image.new("RGBA", (32, 32), color=(0, 0, 0, 0))
    x_off = (32 - cropped_image.width) // 2
    y_off = (32 - cropped_image.height) // 2
    result.paste(cropped_image, (x_off, y_off))

    return result


def second_hand_img(radian) -> Image.Image:
    image = Image.new("RGBA", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
    center_x, center_y = SCALED_WIDTH // 2, SCALED_HEIGHT // 2
    length = 400

    # Calculate the end point of the line based on the radian value
    end_x = center_x + int(length * math.sin(radian))
    end_y = center_y - int(length * math.cos(radian))

    draw = ImageDraw.Draw(image)

    draw.line((center_x, center_y, end_x, end_y), fill="yellow", width=SCALE_FACTOR)

    image = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)
    alpha = image.convert("L")
    result = Image.new("RGBA", image.size)
    result.paste(image)
    result.putalpha(alpha)

    return result


def render_frame(radian, hours_img, mins_img):
    time_image = Image.new("RGBA", (WIDTH, HEIGHT), color=(0, 0, 0, 0))
    time_image.paste(hours_img, box=(0, 0))
    time_image.paste(mins_img, box=(32, 0))
    # return time_image
    ray_image = second_hand_img(radian)
    img = Image.alpha_composite(time_image, ray_image)
    # img = ray_image
    draw = ImageDraw.Draw(img)
    for x in range(32, 33):
        for y in range(11, 13):
            draw.point((x, y), fill="white")
        for y in range(19, 21):
            draw.point((x, y), fill="white")
    return img.convert("RGB")


def datetime_to_radian(t):
    seconds_total = t.second + t.microsecond / 1e6
    return (seconds_total / 60) * 2 * math.pi
