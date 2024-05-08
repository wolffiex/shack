from django.shortcuts import render
from django.http import HttpResponse
import requests
import os
from settings import HA_HOST
import logging

logger = logging.getLogger(__name__)

ha_api_url = f"http://{HA_HOST}:8123/api"
ha_access_token = os.environ["HA_ACCESS_TOKEN"]

def dashboard(request):
    return render(request, "dashboard.html", {})

def start_tidbyt(_):
    current_state = get_switch_state()
    if current_state == "off": 
        new_state = turn_on()
        return HttpResponse(f"Turned on. Now switch is {new_state}", status=200)

    return HttpResponse(f"No action. Switch is {current_state}")

def get_switch_state():
    ha_api_states = ha_api_url + "/states/switch.tidbyt_switch_2"
    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(ha_api_states, headers=headers)
    response.raise_for_status()

    result = response.json()
    return result["state"]

def turn_on():
    ha_api_services = ha_api_url + "/services/switch/turn_on"

    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "entity_id": "switch.tidbyt_switch_2"
    }

    response = requests.post(ha_api_services, headers=headers, json=body)

    response.raise_for_status()
    result = response.json()[0]
    return result["state"]
