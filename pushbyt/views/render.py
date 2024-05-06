from pathlib import Path
from django.http import HttpResponse


# This is not intended to be used in production
def get_render(request, file_name):
    with open(Path("render")/file_name, "rb") as f:
        return HttpResponse(f.read(), content_type="image/webp")

