from django.urls import path
from ha.views import start_tidbyt

urlpatterns = [
    path("start_tidbyt", start_tidbyt, name="start_tidbyt"),
]
