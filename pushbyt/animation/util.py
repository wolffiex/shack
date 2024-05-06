import os
import base64
import requests

TIDBYT_API_PUSH = "https://api.tidbyt.com/v0/devices/%s/push"
def push(image_bytes, device_id, installation_id, background):
    api_token = os.getenv("TIDBYT_TOKEN")

    if not api_token:
        raise ValueError(f"Blank Tidbyt API token (set TIDBYT_TOKEN)")

    payload = {
        "deviceID": device_id,
        "image": base64.b64encode(image_bytes).decode("utf-8"),
        "installationID": installation_id,
        "background": background,
    }

    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(TIDBYT_API_PUSH % device_id, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Tidbyt API returned status {response.status_code}")
        print(response.text)
        raise ValueError(f"Tidbyt API returned status: {response.status_code}")
