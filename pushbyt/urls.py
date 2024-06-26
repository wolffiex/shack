from django.urls import path
from pushbyt.views import (
    get_preview,
    get_player,
    get_render,
    generate,
    get_simulator,
    spotify_login,
    spotify_callback,
    doorbell_ring,
    cleanup,
)

urlpatterns = [
    path("v1/preview.webp", get_preview, name="get_preview"),
    path("player/<str:name>", get_player, name="get_player"),
    path("simulator", get_simulator, name="simulator"),
    path("render/<str:file_name>", get_render, name="get_render"),
    path("spotify/login", spotify_login, name="spotify_login"),
    path("spotify/token", spotify_callback, name="spotify_calllback"),
    path("doorbell", doorbell_ring, name="doorbell_ring"),
    path("command/generate", generate, name="generate"),
    path("command/cleanup", cleanup, name="cleanup"),
]
