from django.shortcuts import redirect
from django.http import HttpResponse
from pushbyt.animation.now_playing import generate
from pushbyt.views.generate import render
from pathlib import Path
from pushbyt.models import Animation
import requests
import os
import logging

logger = logging.getLogger(__name__)


def spotify_env():
    return {
        "redirect_uri": os.environ["SPOTIFY_REDIRECT_URI"],
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
    }


def login(_):
    auth_url = "https://accounts.spotify.com/authorize"
    scope = "user-read-playback-state user-read-currently-playing"
    spotify = spotify_env()

    auth_params = {
        "response_type": "code",
        "client_id": spotify["client_id"],
        "scope": scope,
        "redirect_uri": spotify["redirect_uri"],
    }

    url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in auth_params.items()])}"
    return redirect(url)


def callback(request):
    code = request.GET.get("code")
    token_url = "https://accounts.spotify.com/api/token"
    spotify = spotify_env()

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": spotify["redirect_uri"],
        "client_id": spotify["client_id"],
        "client_secret": spotify["client_secret"],
    }

    response = requests.post(token_url, data=token_data)
    response.raise_for_status()
    logger.info(response)
    access_token = response.json()["access_token"]

    return HttpResponse(f"export SPOTIFY_TOKEN='{access_token}'")


def player(_):
    headers = {
        "Authorization": f"Bearer {os.environ['SPOTIFY_TOKEN']}",
    }
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    data = response.json()
    if not data["device"]["is_active"]:
        return

    # Extract track title
    track_title = data["item"]["name"]

    artist_names = ", ".join(artist["name"] for artist in data["item"]["artists"])

    art_url = None
    for image in data["item"]["album"]["images"]:
        if image["height"] == 64 and image["width"] == 64:
            art_url = image["url"]
            break

    print("Track Title:", track_title)
    print("Artist Names:", artist_names)
    print("64x64 Icon URL:", art_url)
    frames = [*generate(track_title, artist_names, art_url)]
    # last_animation = Animation.objects.latest("start_time")
    # anim_start_time = Animation.align_time(last_animation.start_time_local)
    # file_path = (
    #     Path("render") / anim_start_time.strftime("%j-%H-%M-%S")
    # ).with_suffix(".webp")
    file_path = (Path("render") / "spotify").with_suffix(".webp")
    render(frames, file_path)
    return HttpResponse(file_path)
