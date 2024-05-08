from django.urls import path
from ha.views import start_tidbyt, dashboard, control

urlpatterns = [
    path("start_tidbyt", start_tidbyt, name="start_tidbyt"),
    path("dashboard", dashboard, name="dashboard"),
    path("control/<str:name>", control, name="control"),
]
