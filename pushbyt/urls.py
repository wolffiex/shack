from django.urls import path
from pushbyt.views import get_preview, get_player, get_render, generate

urlpatterns = [
    path("v1/preview.webp", get_preview, name="get_preview"),
    path("player/<str:name>", get_player, name="get_player"),
    path("render/<str:file_name>", get_render, name="get_render"),
    path("command/generate", generate, name="generate"),
]
