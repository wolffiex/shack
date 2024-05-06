from django.views.decorators.cache import cache_control
from pathlib import Path
from django.http import HttpResponse


# This is not intended to be used in production
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def get_render(request, file_name):
    with open(Path("render")/file_name, "rb") as f:
        return HttpResponse(f.read(), content_type="image/webp")

