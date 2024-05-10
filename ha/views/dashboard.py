from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
import os
from settings import HA_HOST
import logging
import psycopg2
import httpx
import asyncio

logger = logging.getLogger(__name__)

ha_api_url = f"http://{HA_HOST}:8123/api"
ha_access_token = os.environ["HA_ACCESS_TOKEN"]
CONTROLS = {
    "tidbyt_switch": ("/services/switch", "switch.tidbyt_switch_2"),
    "heat_switch": ("/services/switch", "switch.space_heater_switch_2"),
    "heat_power": ("/services/script", "script.shack_space_heater_power_on"),
}


def control(request, name):
    api, entity_id = CONTROLS[name]
    action = request.GET.get("action", "")
    post_ha_action(api, action, entity_id)
    return redirect("dashboard")


def post_ha_action(api, action, entity_id):
    url = ha_api_url + api + "/" + action
    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json",
    }
    data = {"entity_id": entity_id}
    response = httpx.post(url, headers=headers, json=data)
    response.raise_for_status()


async def dashboard(request):
    ha_data = await ha_info()
    monitoring_data = get_monitoring()
    return render(request, "dashboard.html", ha_data | monitoring_data)


async def ha_info():
    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        urls = [
            ha_api_url + "/states/switch.tidbyt_switch_2",
            ha_api_url + "/states/switch.space_heater_switch_2",
            ha_api_url + "/states/sensor.space_heater_power_2",
        ]
        responses = await asyncio.gather(
            *[client.get(url, headers=headers) for url in urls]
        )
        t_switch, h_switch, h_power = [
            response.json()["state"] for response in responses
        ]
        return {
            "tidbyt_switch": convert_switch_state(t_switch),
            "heat_switch": convert_switch_state(h_switch),
            "heat_power": h_power,
        }


def convert_switch_state(switch_state):
    assert switch_state in ["on", "off"]
    return switch_state == "on"


def get_monitoring():
    with psycopg2.connect(
        "dbname=monitoring user=adam host=spine password=adam"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select co2, temperature, humidity, time from air order by time desc limit 1;"
            )
            result = cur.fetchone()
            assert result
            co2, celsius, humidity, air_time = result

            cur.execute("""
                SELECT time, detected FROm motion ORDER BY time desc LIMIT 10
            """)

            results = cur.fetchall()

            motion_spans = []
            current_span_end = None
            for time, detected in results:
                if not detected:
                    current_span_end = time
                elif current_span_end:
                    motion_spans.append((time, current_span_end-time))
                    current_span_end = None

    farenheight = celsius * 9 / 5 + 32
    return {
        "co2": f"{co2} ppm",
        "temperature": f"{round(farenheight)}° F",
        "humidity": f"{round(humidity)} %",
        "air_time": air_time,
        "motion_spans": motion_spans,
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
        "Content-Type": "application/json",
    }

    response = requests.get(ha_api_states, headers=headers)
    response.raise_for_status()

    result = response.json()
    return result["state"]


def turn_on():
    ha_api_services = ha_api_url + "/services/switch/turn_on"

    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json",
    }

    body = {"entity_id": "switch.tidbyt_switch_2"}

    response = requests.post(ha_api_services, headers=headers, json=body)

    response.raise_for_status()
    result = response.json()[0]
    return result["state"]
