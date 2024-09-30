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
    time_image = Image.new("RGBA", (WIDTH, HEIGHT), color="black")
    time_image.paste(hours_img, box=(0, 0))
    time_image.paste(mins_img, box=(32, 0))
    time_pix: dict[tuple[int,int] , bool] = dict()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            p = x, y
            if time_image.getpixel(p) != (0,0,0,0):
                time_pix[p] = False
    while True:
        yield render_frame(datetime_to_radian(t), time_pix)

        t += FRAME_TIME


def get_time_img(font, text):
    image = Image.new("RGBA", (32, 32), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    text_position = (0, 0)
    # text_width, text_height = draw.textsize(text, font=font)
    # text_position = ((32 - text_width) // 2, (32 - text_height) // 2)
    draw.text(text_position, text, font=font, fill="white")

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
    image = Image.new("RGBA", (SCALED_WIDTH, SCALED_HEIGHT), color="black")
    center_x, center_y = SCALED_WIDTH // 2, SCALED_HEIGHT // 2
    length = 400

    # Calculate the end point of the line based on the radian value
    end_x = center_x + int(length * math.sin(radian))
    end_y = center_y - int(length * math.cos(radian))

    draw = ImageDraw.Draw(image)

    draw.line((center_x, center_y, end_x, end_y), fill="yellow", width=SCALE_FACTOR)

    image = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)

    return image

def render_frame(radian, time_pix):
    ray_image = second_hand_img(radian)

    alpha = ray_image.convert("L")
    # Create a list of non-black points and sort them by distance from the center
    non_black_points = []
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if alpha.getpixel((x, y)) != 0:
                non_black_points.append((x, y))

    # Sort the non-black points by distance from the center
    non_black_points.sort(key=lambda point: 
        math.sqrt((point[0] - center_x) ** 2 + (point[1] - center_y) ** 2))

    i = 1.0
    for p in non_black_points:
        value = alpha.getpixel(p)
        if p in time_pix:
            if not time_pix[p] and value > 150:
                i -= .4
                time_pix[p] = True
        new_value = int(value * max(0, i))
        alpha.putpixel(p, new_value)

    time_image = Image.new("RGBA", (WIDTH, HEIGHT), color="black")
    time_draw = ImageDraw.Draw(time_image)
    for p in time_pix:
        if time_pix[p]:
            time_draw.point(p, fill=(0, 255,255, 255))

    masked_ray = Image.new("RGBA", ray_image.size)
    masked_ray.paste(ray_image)
    masked_ray.putalpha(alpha)

    img = Image.alpha_composite(time_image, masked_ray)
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
