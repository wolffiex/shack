# Re-authorizing Spotify (headless)

The Spotify integration (`pushbyt/spotify.py`) uses a refresh token stored in the
`ApiToken` model to mint short-lived access tokens. If that refresh token is
revoked or expires, `get_access_token()` starts failing with
`400 Bad Request` (`invalid_grant`) and Spotify animations stop.

Recovering requires a fresh OAuth consent — there is no non-interactive way to
revive a dead refresh token. Use the `spotify_auth` management command.

## Why the in-app `/spotify/login` flow doesn't work here

Spotify now rejects non-loopback `http://` redirect URIs as "insecure". The
`SPOTIFY_REDIRECT_URI` in `.env` (`http://spine/...`) is no longer accepted, and
this box is headless with no browser. The workaround below uses an explicit
`127.0.0.1` loopback redirect (still allowed over http) and doesn't need anything
listening on it — the authorization code shows up in the browser's address bar.

## Steps

1. Add this redirect URI in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   for the app, and save:

   ```
   http://127.0.0.1:8888/callback
   ```

2. On the box, print the authorize URL:

   ```
   python manage.py spotify_auth
   ```

3. Open that URL in a browser on any machine, approve. The browser will try to
   load `http://127.0.0.1:8888/callback?code=...` and fail to connect — that's
   expected. Copy the `code` value from the address bar.

4. Exchange the code (do this promptly — codes expire quickly):

   ```
   python manage.py spotify_auth --code <code>
   ```

   This saves a new `ApiToken` with a fresh refresh token. The running server
   reads the same database, so Spotify animations resume on the next generate
   cycle — no restart needed.

## Verifying

```
python manage.py shell -c "from pushbyt.spotify import now_playing; print(now_playing())"
```

A dict (or `None` when nothing is playing) means it's working; a traceback means
the token is still bad.
