from django.urls import path

from .views import summary_api

app_name = "dashboard_api"

urlpatterns = [
    path("summary/", summary_api, name="summary"),
]
