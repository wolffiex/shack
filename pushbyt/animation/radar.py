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
    while True:
        yield render_frame(datetime_to_radian(t), time_image)

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

    draw.line((center_x, center_y, end_x, end_y), fill="white", width=SCALE_FACTOR)

    image = image.resize((WIDTH, HEIGHT), resample=Image.LANCZOS)

    return image

alpha = Image.new("L", (WIDTH, HEIGHT))
def render_frame(radian, time_image):
    global alpha
    ray_image = second_hand_img(radian)
    time_image_copy = time_image.copy()

    original_alpha = time_image.getchannel("A")
    new_alpha = ImageChops.multiply(ray_image, original_alpha)
    alpha = Image.eval(alpha, lambda x: int(x * 0.99))
    alpha = ImageChops.screen(alpha, new_alpha)

    # Apply the new alpha to the copy of time_image
    time_image_copy.putalpha(alpha)

    background = Image.new("RGBA", ray_image.size)
    background.paste(ray_image)

    img = Image.alpha_composite(background, time_image_copy)
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

    # alpha = ray_image.convert("L")
    # # Create a list of non-black points and sort them by distance from the center
    # non_black_points = []
    # center_x, center_y = WIDTH // 2, HEIGHT // 2
    # for y in range(HEIGHT):
    #     for x in range(WIDTH):
    #         if alpha.getpixel((x, y)) != 0:
    #             non_black_points.append((x, y))

    # # Sort the non-black points by distance from the center
    # non_black_points.sort(key=lambda point: 
    #     math.sqrt((point[0] - center_x) ** 2 + (point[1] - center_y) ** 2))
    # for p in non_black_points:
    #     value = alpha.getpixel(p)
    #     if p in time_pix:
    #         # time_pix[p] = min(255, time_pix[p] + value)
    #         pass

