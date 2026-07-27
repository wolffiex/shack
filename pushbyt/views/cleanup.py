from pushbyt.models import Animation
import logging
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta
from urllib.parse import urlencode
import subprocess

logger = logging.getLogger(__name__)


@require_POST
def clear_queue(request):
    """Drop queued animations so the next generate rebuilds immediately.
    POST+redirect so a reload doesn't re-run it."""
    deleted, _ = Animation.queued().delete()
    logger.info(f"Cleared {deleted} queued animations")

    source = request.POST.get("source", "")
    query = f"?{urlencode({'source': source})}" if source else ""
    return redirect(reverse("simulator") + query)


def cleanup(_):
    command = "find render -type f -cmin +240 -delete -print | wc -l"
    four_hours_ago = timezone.now() - timedelta(hours=4)
    try:
        output = subprocess.check_output(command, shell=True, text=True)

        find_msg = f"Number of files deleted: {output.strip()}"
        logger.info(find_msg)

        deleted_animations = Animation.objects.filter(
            created_at__lt=four_hours_ago
        ).delete()
        deleted_count = deleted_animations[0] if deleted_animations else 0
        model_msg = f"Number of Animation models deleted: {deleted_count}"
        logger.info(model_msg)
        return HttpResponse("\n".join([find_msg, model_msg]))
    except subprocess.CalledProcessError as e:
        error_msg = f"Error occurred while running the command: {e}"
        logger.error(error_msg)
        return HttpResponseServerError(error_msg)
