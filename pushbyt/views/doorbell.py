from pushbyt.models import Animation
import logging
from pathlib import Path
from django.http import HttpResponse

logger = logging.getLogger(__name__)
DOORBELL_PATH = (Path("render") / "doorbell").with_suffix(".webp")


def doorbell_ring(_):
    anim = Animation(
        file_path=DOORBELL_PATH, source=Animation.Source.DOORBELL, metadata={})
    anim.save()
    return HttpResponse("ok")
