from django.urls import path
from ha.views import (
    start_tidbyt, dashboard, control, start_timer, cancel_timer
)

urlpatterns = [
    path("start_tidbyt", start_tidbyt, name="start_tidbyt"),
    path("dashboard", dashboard, name="dashboard"),
    path("control/<str:name>", control, name="control"),
    path("timer/start", start_timer, name="start_timer"),
    path("timer/cancel", cancel_timer, name="cancel_timer"),
]
