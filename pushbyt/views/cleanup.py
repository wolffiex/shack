from pushbyt.models import Animation
import logging
from django.http import HttpResponse, HttpResponseServerError
from django.utils import timezone
from datetime import timedelta
import subprocess

logger = logging.getLogger(__name__)


def cleanup(_):
    command = "find render -type f -cmin +240 -delete -print | wc -l"
    four_hours_ago = timezone.now() - timedelta(hours=4)
    try:
        output = subprocess.check_output(command, shell=True, text=True)

        find_msg = f"Number of files deleted: {output.strip()}"
        logger.info(find_msg)

        deleted_animations = Animation.objects.filter(
            created_at__lt=four_hours_ago).delete()
        deleted_count = deleted_animations[0] if deleted_animations else 0
        model_msg = f"Number of Animation models deleted: {deleted_count}"
        logger.info(model_msg)
        return HttpResponse("\n".join([find_msg, model_msg]))
    except subprocess.CalledProcessError as e:
        error_msg = f"Error occurred while running the command: {e}"
        logger.error(error_msg)
        return HttpResponseServerError(error_msg)
