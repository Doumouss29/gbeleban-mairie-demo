from django.urls import path

from . import views

app_name = "siteanalytics"

urlpatterns = [
    path("statistiques/", views.dashboard, name="dashboard"),
    path("track-click/", views.track_click, name="track_click"),
]
