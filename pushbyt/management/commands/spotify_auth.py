from django_rich.management import RichCommand
from urllib.parse import urlencode
import requests
from pushbyt.spotify import spotify_env, TOKEN_URL
from pushbyt.models import ApiToken


# Spotify now rejects non-loopback http redirect URIs as "insecure", so we use
# an explicit 127.0.0.1 loopback address. Nothing needs to listen on it: the
# authorization code lands in the browser's address bar and is pasted back via
# --code (see docs/spotify-reauth.md).
DEFAULT_REDIRECT = "http://127.0.0.1:8888/callback"
SCOPE = "user-read-playback-state user-read-currently-playing"


class Command(RichCommand):
    help = "Re-authorize Spotify on a headless box (mint a fresh refresh token)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--code",
            help="Authorization code copied from the redirect URL after approving",
        )
        parser.add_argument(
            "--redirect-uri",
            default=DEFAULT_REDIRECT,
            help=f"Redirect URI registered in the Spotify dashboard (default: {DEFAULT_REDIRECT})",
        )

    def handle(self, *args, **options):
        redirect_uri = options["redirect_uri"]
        code = options["code"]
        spotify = spotify_env()

        if not code:
            params = {
                "response_type": "code",
                "client_id": spotify["client_id"],
                "scope": SCOPE,
                "redirect_uri": redirect_uri,
            }
            url = "https://accounts.spotify.com/authorize?" + urlencode(params)
            self.console.print(
                f"1. Register this redirect URI in the Spotify dashboard: {redirect_uri}",
                style="bold",
            )
            self.console.print(
                "2. Open this URL in a browser, approve, then copy the ?code= value "
                "from the address bar (the page failing to load is fine):",
                style="bold",
            )
            self.console.print(url)
            self.console.print(
                "3. Re-run: python manage.py spotify_auth --code <code>", style="bold"
            )
            return

        request_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": spotify["client_id"],
            "client_secret": spotify["client_secret"],
        }
        response = requests.post(TOKEN_URL, data=request_data)
        response.raise_for_status()
        payload = response.json()
        token = ApiToken(
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            expires_in=payload["expires_in"],
        )
        token.save()
        self.console.print(
            f"Saved ApiToken pk {token.pk} (expires_in {token.expires_in}s)",
            style="bold green",
        )
