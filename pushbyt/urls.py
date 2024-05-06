from django.urls import path
from pushbyt.views import get_preview, get_player, get_render, generate, get_simulator

urlpatterns = [
    path("v1/preview.webp", get_preview, name="get_preview"),
    path("player/<str:name>", get_player, name="get_player"),
    path("command/generate", generate, name="generate"),
    path("simulator", get_simulator, name="simulator"),
    path("render/<str:file_name>", get_render, name="get_render"),
]
