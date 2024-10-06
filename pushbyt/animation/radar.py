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

def create_oversample_alpha_mask():
    """Create a mask that is opaque in the center and transparent at the edges."""
    mask = Image.new("L", (WIDTH, HEIGHT), color=255)  # Start with fully opaque
    draw = ImageDraw.Draw(mask)

    center_x, center_y = WIDTH // 2, HEIGHT // 2
    max_radius = min(center_x, center_y)

    for radius in range(max_radius):
        alpha_value = int(255 * (1 - (radius / max_radius)))  # Opaque in the center, fades to transparent
        draw.ellipse(
            (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
            outline=alpha_value,
            fill=None
        )
    return mask

def render_frame(radian, time_image):
    global alpha
    ray_image = second_hand_img(radian)
    time_image_copy = time_image.copy()

    # Get the original alpha (transparency) of the time image (the time digits)
    original_alpha = time_image.getchannel("A")
    
    # Apply the radial oversampling mask to the alpha channel of the numbers
    oversample_mask = create_oversample_alpha_mask()
    enhanced_alpha = ImageChops.multiply(original_alpha, oversample_mask)

    # Multiply ray_image with the enhanced alpha channel
    new_alpha = ImageChops.multiply(ray_image, enhanced_alpha)

    # Decay the alpha over time to create the fading effect
    alpha = Image.eval(alpha, lambda x: int(x * 0.99))

    # Screen the new alpha with the decayed alpha
    alpha = ImageChops.screen(alpha, new_alpha)

    # Apply the updated alpha to the time image copy
    time_image_copy.putalpha(alpha)

    # Create a new blank background
    background = Image.new("RGBA", ray_image.size)

    # Paste the ray_image (second hand) onto the background
    background.paste(ray_image)

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
