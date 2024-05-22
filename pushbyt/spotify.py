import base64
import requests
from django.utils import timezone
from datetime import timedelta
from pushbyt.models import ApiToken
import logging
import os

logger = logging.getLogger(__name__)

TOKEN_URL = "https://accounts.spotify.com/api/token"


def spotify_env():
    return {
        "redirect_uri": os.environ["SPOTIFY_REDIRECT_URI"],
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
    }


def get_access_token() -> str:
    token = ApiToken.objects.latest("created_at")
    if token.updated_at + timedelta(seconds=token.expires_in) < timezone.now():
        logger.info("Refreshing Spotify access")
        spotify = spotify_env()

        client_id = spotify["client_id"]
        client_secret = spotify["client_secret"]

        auth_header = base64.b64encode(
            f"{client_id}:{client_secret}".encode()).decode()

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
    response = requests.get(
        "https://api.spotify.com/v1/me/player", headers=headers)
    response.raise_for_status()
    if not response.text.strip():
        return
    data = response.json()
    if not data["device"]["is_active"]:
        return

    # Extract track title
    track_title = data["item"]["name"]
    track_id = data["item"]["id"]

    artist_names = ", ".join(artist["name"]
                             for artist in data["item"]["artists"])

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
