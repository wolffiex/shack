import tempfile
import subprocess
from PIL import Image, ImageDraw, ImageFont
from abc import ABC, abstractmethod
from typing import Generator
from pathlib import Path
from datetime import datetime, timedelta


class FrameGenerator(ABC):
    FRAME_TIME: timedelta = timedelta(milliseconds=100)
    WIDTH = 64
    HEIGHT = 32

    def __init__(self, start_time: datetime):
        self.start_time = start_time
        self.frames = self._gen_frames()

    @abstractmethod
    def _gen_frames(self) -> Generator[Image.Image, None, None]:
        pass

    def save(self, file_path: Path, duration: timedelta) -> bool:
        t_delta = timedelta(0)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            frames_arg = []
            frame_num = 0
            ended = False
            while t_delta + self.FRAME_TIME * frame_num < duration:
                try:
                    frame = next(self.frames)
                except StopIteration:
                    ended = True
                    break
                frame_file = temp_path / f"frame{frame_num:04d}.webp"
                frame.save(frame_file, "WebP", quality=100)
                frames_arg.append(
                    f"-frame {frame_file} +{self.FRAME_TIME.total_seconds() * 1000}"
                )
                frame_num += 1
            cmd = f"webpmux {" ".join(frames_arg)} -loop 1 -bgcolor 255,255,255,255 -o {file_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
            return ended


class Spritz(FrameGenerator):
    FRAME_TIME = timedelta(milliseconds=120)
    TEXT_TOP = FrameGenerator.HEIGHT /2 - 4
    TEXT_MID = FrameGenerator.WIDTH // 3

    def __init__(self, start_time: datetime, copy):
        self.start_time = start_time
        self.frames = self._gen_frames()
        self.tokens = self.tokenize(copy)

    def _gen_frames(self):
        font = ImageFont.truetype("./fonts/pixelmix/pixelmix.ttf", 8)
        for token in self.tokens:
            yield self.render(token, font)

    def render(self, token:str, font) -> Image.Image:
        # print(f"|{token}|")
        start, mid, end = self.word_split(token)
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), color="black")
        draw = ImageDraw.Draw(image)
        mid_width = self.measure(mid, font)
        mid_left = self.TEXT_MID - mid_width // 2
        draw.text((mid_left, self.TEXT_TOP), mid, font=font, fill=(255, 50, 50))
        if start:
            start_width = self.measure(start, font)
            start_left = mid_left - start_width
            draw.text((start_left, self.TEXT_TOP), start, font=font, fill="white")
        if end:
            end_left = mid_left + mid_width
            draw.text((end_left, self.TEXT_TOP), end, font=font, fill="white")
        return image

    def word_split(self, token:str):
        token_len = len(token)
        if token_len == 1:
            return "", token, ""
        elif token_len == 2:
            return token[0], token[1], ""
        elif token_len < 5:
            return token[0], token[1], token[2:]
        elif token_len < 7:
            return token[0:2], token[2], token[3:]
        else:
            return token[0:3], token[3], token[4:]

    def measure(self, text:str, font) -> int:
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), color="black")
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=font)
        left, _, right, _ = bbox
        return right - left

    def tokenize(self, copy: str) -> Generator[str, None, None]:
        last_token = ""
        for token in copy.split(" "):
            if not self.is_word(last_token):
                last_token += token
            elif self.is_word(token):
                yield last_token
                last_token = token
            else:
                last_token += f" {token}"
        if last_token:
            yield last_token

    def is_word(self, token: str) -> bool:
        return bool(token)


text_copy = """Baking the chicken wings at 375 degrees F for one hour instead of 400 degrees F for 45 minutes is a reasonable adjustment and can work well, depending on your preferences. Here are a few considerations for using this approach:

Gentler Cooking: Lowering the temperature and increasing the cooking time can result in a gentler cook, which might be beneficial if you want to ensure the wings are thoroughly cooked without the risk of burning or drying out the exterior too quickly. This can be especially useful if your oven tends to run hot.
Texture: The skin might not become as crisply as it would at a higher temperature, but it should still achieve a good texture, particularly with the second bake to crisp up the skin.
Even Cooking: A longer, slower bake can help the meat cook more evenly, which can be great for texture and juiciness.
Final Crispiness: Since the initial bake at a lower temperature might leave the skin less crispy, you'll want to ensure that the second bake (especially if you’re adding a glaze or sauce) really focuses on achieving that crisp finish. You might consider increasing the temperature slightly during the second bake or even using the broil setting for the last few minutes to help crisp up the skin.
This adjustment can be a good way to adapt the recipe to your specific oven and preferences. Just keep an eye on the wings towards the end of the cooking time to ensure they are cooked through and have achieved your desired level of crispiness before proceeding with the second bake.
"""

if __name__ == "__main__":
    spritz = Spritz(datetime.now(), text_copy)
    i = 0
    finished = False
    while not finished:
        finished = spritz.save(Path("dist") / f"spritz{i}.webp", timedelta(seconds=15))
        i += 1
    print(finished)
