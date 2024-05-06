from django.utils import timezone
from django.shortcuts import redirect
from pushbyt.models import Animation
import logging

logger = logging.getLogger(__name__)


def get_preview(_):
    now = timezone.now()
    anim = Animation.get_next_animation(now)
    if anim:
        if anim.served_at:
            logger.error(
                f"Already served {anim.file_path} at {anim.served_at} now {now}"
            )
    else:
        anim = Animation(start_time=Animation.align_time(now))
    anim.served_at = now
    anim.save()
    return redirect(anim.url)
