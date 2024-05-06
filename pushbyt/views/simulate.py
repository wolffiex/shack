from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


def get_simulator(request):
    return render(request, "simulator.html")
