from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from ha.models import Timer
from datetime import timedelta

import logging

logger = logging.getLogger(__name__)


@require_POST
def start_timer(request):
    timer_value = request.POST.get('timerValue')

    if timer_value:
        timer = Timer(duration=timedelta(minutes=int(timer_value)))
        timer.save()

        return redirect("dashboard")

    # If the timer value is not provided or invalid, redirect back to the form
    return redirect("dashboard")
