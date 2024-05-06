from PIL import Image, ImageDraw, ImageFont
import random

width, height = 64, 32
frames = []
duration = 100  # ms per frame (10fps)

def generate_coordinates(right, bottom):
    return ((x, y) for x in range(right) for y in range(bottom))

text = "Hello, World!"
text_color = (255, 0, 0)  # Red color
image = Image.new('RGB', (width, height), color='black')
font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
draw = ImageDraw.Draw(image)
text_position = (0, 0)
bbox = draw.textbbox(text_position, text, font=font)
draw.text(text_position, text, font=font, fill='white')
left, top, right, bottom = bbox
pixels = image.load()
print("Bounding box coordinates (left, top, right, bottom):", bbox)
filtered_coordinates = ((x, y) for x in range(right) for y in range(bottom) if pixels[x, y] != (0, 0, 0))
frames = [Image.new('RGB', (width, height), color='black')]
filtered_coordinates_list = list(filtered_coordinates)

# Shuffle the list
random.shuffle(filtered_coordinates_list)
for point in filtered_coordinates_list:
    last_frame = frames[-1]
    frame = last_frame.copy()
    frame.putpixel(point, pixels[point])
    frames.append(frame)
    # print(f"({x},{y}) {pixels[x, y]}" )

for _ in range(20):
    frames.append(frames[-1])

frames[0].save('animation.webp', save_all=True, append_images=frames[1:],
               duration=duration, loop=0, quality=100)
