import os
import httpx
import logging
from settings import HA_HOST

logger = logging.getLogger(__name__)
ha_api_url = f"http://{HA_HOST}:8123/api"
ha_access_token = os.environ["HA_ACCESS_TOKEN"]


def tidbyt_turn_on():
    url = ha_api_url + "/services/switch/turn_on"
    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json",
    }
    data = {"entity_id": "switch.tidbyt_switch_2"}
    response = httpx.post(url, headers=headers, json=data)
    response.raise_for_status()
