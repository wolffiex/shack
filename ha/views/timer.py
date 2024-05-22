from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from ha.models import Timer
from pushbyt.animation import update_timer
from datetime import timedelta

import logging

logger = logging.getLogger(__name__)


@require_POST
def start_timer(request):
    timer_value = request.POST.get('minutes')
    timer = Timer(duration=timedelta(minutes=int(timer_value)))
    timer.save()
    update_timer()
    return redirect("dashboard")


@require_POST
def cancel_timer(request):
    timer_pk = request.POST.get('timerPk')
    timer = Timer.objects.get(pk=timer_pk)
    timer.canceled = True
    timer.save()
    update_timer()
    return redirect("dashboard")
