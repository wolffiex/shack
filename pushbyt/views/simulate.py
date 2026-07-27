from django.shortcuts import render
from pushbyt.animation.generate import CLOCK_SOURCES
from pushbyt.views.generate import parse_clock_source
import logging

logger = logging.getLogger(__name__)


def get_simulator(request):
    """Selection lives in ?source=, not client state."""
    source = parse_clock_source(request)
    return render(
        request,
        "simulator.html",
        {
            "clock_source": source.value if source else "",
            "clock_sources": CLOCK_SOURCES,
        },
    )
