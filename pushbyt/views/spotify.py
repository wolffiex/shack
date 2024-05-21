from django.shortcuts import redirect
from urllib.parse import urlencode
import requests
import logging
from pushbyt.spotify import spotify_env, TOKEN_URL
from pushbyt.models import ApiToken

logger = logging.getLogger(__name__)


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
