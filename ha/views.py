from django.shortcuts import render
from django.http import HttpResponse
import requests
import os
from settings import HA_HOST
import logging
import psycopg2

logger = logging.getLogger(__name__)

ha_api_url = f"http://{HA_HOST}:8123/api"
ha_access_token = os.environ["HA_ACCESS_TOKEN"]
conn = psycopg2.connect("dbname=monitoring user=adam host=spine password=adam")

def dashboard(request):
    data =  latest_air()
    return render(request, "dashboard.html", data)

def latest_air():
    with conn.cursor() as cur:
        cur.execute(
            "select co2, temperature, humidity from air order by time desc limit 1;"
        )
        result = cur.fetchone()
        assert result
        co2, celsius, humidity = result

    farenheight = celsius *  9/5 + 32
    return {
        "co2": f"{co2} ppm",
        "temperature": f"{round(farenheight)}° F",
        "humidity": f"{round(humidity)} %",
    }

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
