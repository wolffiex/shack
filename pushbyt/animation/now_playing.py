from PIL import Image, ImageDraw, ImageFont, ImageChops
from typing import Generator, Optional
from io import BytesIO
import requests


WIDTH, HEIGHT = 64, 32

def generate(track:str, artist:str, art_url:Optional[str]) -> Generator[Image.Image, str, None]:
    # black_image = Image.new("RGB", (WIDTH, HEIGHT), color="black")
    if not art_url:
        raise ValueError("Missing art not handled")
    response = requests.get(art_url)
    art_data = response.content
    art = Image.open(BytesIO(art_data))

    for top in range(0, 32):
        frame = art.copy()
        yield frame.crop((0, top, 64, top+32))
