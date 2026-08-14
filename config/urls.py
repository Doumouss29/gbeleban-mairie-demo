from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("pilotage-projets/", include("pilotage.urls")),
    path("analytics/", include("siteanalytics.urls")),
    path("", include("portal.urls")),
]
