from django.shortcuts import render, redirect
from django.urls import reverse
from asgiref.sync import sync_to_async
from django.http import HttpResponse
from django.utils import timezone
from ha.models import Timer
from urllib.parse import quote
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
    "security_light_switch": ("/services/switch", "switch.security_light_switch_2"),
    "fountain_switch": ("/services/switch", "switch.fountain_switch_2"),
}


def control(request, name):
    api, entity_id = CONTROLS[name]
    action = request.GET.get("action", "")
    try:
        post_ha_action(api, action, entity_id)
    except Exception as e:
        error_message = quote(str(e))
        return redirect(reverse("dashboard") + f"?error_message={error_message}")

    return redirect("dashboard")


def post_ha_action(api, action, entity_id):
    url = ha_api_url + api + "/" + action
    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json",
    }
    data = {"entity_id": entity_id}
    response = httpx.post(url, headers=headers, json=data, timeout=5.0)
    response.raise_for_status()


async def dashboard(request):
    error_data = {"error_message": request.GET.get("error_message", "")}

    try:
        ha_data = await ha_info()
    except Exception as e:
        logger.error(f"Error getting HA data: {e}")
        ha_data = {
            "tidbyt_switch": False,
            "heat_switch": False,
            "heat_power": "unavailable",
            "security_light_switch": False,
            "fountain_switch": False,
        }

    try:
        monitoring_data = get_monitoring()
    except Exception as e:
        logger.error(f"Error getting monitoring data: {e}")
        monitoring_data = {
            "co2": "-- ppm",
            "temperature": "--° F",
            "humidity": "-- %",
            "air_delay": "unavailable",
        }

    try:
        timer_data = await get_timer()
    except Exception as e:
        logger.error(f"Error getting timer data: {e}")
        timer_data = {"timer": None}

    return render(
        request, "dashboard.html", (ha_data | monitoring_data | timer_data | error_data)
    )


@sync_to_async
def get_timer():
    timer = Timer.objects.order_by("-created_at").first()
    if timer and not timer.is_running:
        timer = None
    return {"timer": timer}


async def ha_info():
    headers = {
        "Authorization": f"Bearer {ha_access_token}",
        "Content-Type": "application/json",
    }

    # Use custom timeout with more generous connect timeout
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(10.0, connect=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            urls = [
                ha_api_url + "/states/switch.tidbyt_switch_2",
                ha_api_url + "/states/switch.space_heater_switch_2",
                ha_api_url + "/states/sensor.space_heater_power_2",
                ha_api_url + "/states/switch.security_light_switch_2",
                ha_api_url + "/states/switch.fountain_switch_2",
            ]

            # Individual requests with error handling instead of gather
            responses = []
            for url in urls:
                try:
                    response = await client.get(url, headers=headers)
                    responses.append(response)
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")

                    # Create a mock response
                    class MockResponse:
                        def json(self):
                            return {"state": "unknown"}

                    responses.append(MockResponse())

            # Ensure we have exactly 5 responses
            while len(responses) < 5:

                class MockResponse:
                    def json(self):
                        return {"state": "unknown"}

                responses.append(MockResponse())

            t_switch, h_switch, h_power, security_light, fountain = [
                response.json()["state"] for response in responses
            ]

            # Handle unknown states
            return {
                "tidbyt_switch": convert_switch_state(t_switch)
                if t_switch != "unknown"
                else False,
                "heat_switch": convert_switch_state(h_switch)
                if h_switch != "unknown"
                else False,
                "heat_power": h_power if h_power != "unknown" else "0",
                "security_light_switch": convert_switch_state(security_light)
                if security_light != "unknown"
                else False,
                "fountain_switch": convert_switch_state(fountain)
                if fountain != "unknown"
                else False,
            }

    except Exception as e:
        logger.error(f"Error in ha_info: {e}")
        return {
            "tidbyt_switch": False,
            "heat_switch": False,
            "heat_power": "0",
            "security_light_switch": False,
            "fountain_switch": False,
        }


def convert_switch_state(switch_state):
    if switch_state not in ["on", "off", "unknown"]:
        logger.warning(f"Unexpected switch state: {switch_state}")
        return False
    return switch_state == "on"


def get_monitoring():
    try:
        # Add connection timeout
        with psycopg2.connect(
            "dbname=monitoring user=adam host=spine password=adam connect_timeout=5"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select co2, temperature, humidity, time from air order by time desc limit 1;"
                )
                result = cur.fetchone()
                if result:
                    co2, celsius, humidity, air_time = result
                    farenheight = celsius * 9 / 5 + 32
                    air_delay = timezone.now() - air_time
                    return {
                        "co2": f"{round(co2)} ppm",
                        "temperature": f"{round(farenheight)}° F",
                        "humidity": f"{round(humidity)} %",
                        "air_delay": f"{round(air_delay.total_seconds())} seconds ago",
                    }
    except Exception as e:
        logger.error(f"Error in get_monitoring: {e}")

    # Return default values if database connection fails
    return {
        "co2": "-- ppm",
        "temperature": "--° F",
        "humidity": "-- %",
        "air_delay": "unavailable",
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

    response = requests.get(ha_api_states, headers=headers, timeout=5.0)
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

    response = requests.post(ha_api_services, headers=headers, json=body, timeout=5.0)

    response.raise_for_status()
    result = response.json()[0]
    return result["state"]
