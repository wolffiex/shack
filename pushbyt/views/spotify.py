from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from pushbyt.animation.now_playing import generate
from pushbyt.views.generate import render
from pathlib import Path
from pushbyt.models import Animation
from urllib.parse import urlencode
import requests
import os
import logging
import base64
from pushbyt.models import ApiToken

logger = logging.getLogger(__name__)


TOKEN_URL = "https://accounts.spotify.com/api/token"


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

    url = f"{auth_url}?{urlencode(auth_params)}"
    return redirect(url)


def callback(request):
    code = request.GET.get("code")
    spotify = spotify_env()

    request_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": spotify["redirect_uri"],
        "client_id": spotify["client_id"],
        "client_secret": spotify["client_secret"],
    }

    response = requests.post(TOKEN_URL, data=request_data)
    response.raise_for_status()
    token = ApiToken(
        access_token=response.json()["access_token"],
        refresh_token=response.json()["refresh_token"],
        expires_in=response.json()["expires_in"],
    )
    token.save()
    return redirect("dashboard")


def get_access_token() -> str:
    token = ApiToken.objects.latest("created_at")
    if token.updated_at + timedelta(seconds=token.expires_in) < timezone.now():
        logger.info("Refreshing Spotify access")
        spotify = spotify_env()

        client_id = spotify["client_id"]
        client_secret = spotify["client_secret"]

        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        request_data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }
        headers = {
            "Authorization": f"Basic {auth_header}",
        }
        response = requests.post(TOKEN_URL, headers=headers, data=request_data)
        response.raise_for_status()
        token.access_token = response.json()["access_token"]
        token.expires_in = response.json()["expires_in"]
        token.save()
    return token.access_token


def now_playing():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    response.raise_for_status()
    if not response.text.strip():
        return
    data = response.json()
    if not data["device"]["is_active"]:
        return

    # Extract track title
    track_title = data["item"]["name"]
    track_id = data["item"]["id"]

    artist_names = ", ".join(artist["name"] for artist in data["item"]["artists"])

    art_url = None
    for image in data["item"]["album"]["images"]:
        if image["height"] == 64 and image["width"] == 64:
            art_url = image["url"]
            break

    return {
        "id": track_id,
        "title": track_title,
        "artist": artist_names,
        "art": art_url,
    }


def player(_):
    track_info = now_playing()
    logger.info(track_info)
    track_info = {
        "id": "xxxx4ZpQiJ78LKINrW9SQTgbXdxxxx",
        "title": "Take My Hand title: Take My Hand",
        "artist": "Dido last_animation = Animation.objects.latest( wstart_time )",
        "art": "https://i.scdn.co/image/ab67616d00004851f655ea5e71413d83c51b9687",
    }
    assert track_info
    frames = [*generate(track_info["title"], track_info["artist"], track_info["art"])]
    # last_animation = Animation.objects.latest("start_time")
    # anim_start_time = Animation.align_time(last_animation.start_time_local)
    # file_path = (
    #     Path("render") / anim_start_time.strftime("%j-%H-%M-%S")
    # ).with_suffix(".webp")
    file_path = (Path("render") / "spotify").with_suffix(".webp")
    render(frames, file_path)
    return HttpResponse(file_path)
