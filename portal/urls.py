from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("projets/", views.projects, name="projects"),
    path("actualites/", views.news, name="news"),
    path("pages/<slug:slug>/", views.page_detail, name="page_detail"),
    path("gbeleban-en-carte/", views.map_public, name="map_public"),
    path("api/couches/<int:layer_id>.geojson", views.layer_geojson, name="layer_geojson"),
    path("urbanisme/", views.urbanism, name="urbanism"),
    path("api/cadastre.geojson", views.parcels_geojson, name="parcels_geojson"),
    path("api/cadastre/recherche/", views.parcel_search, name="parcel_search"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("gestion/", views.management_home, name="management_home"),
    path("gestion/sig/import/", views.import_geojson_view, name="import_geojson"),
    path("gestion/cadastre/import/", views.import_cadastre_view, name="import_cadastre"),
]
