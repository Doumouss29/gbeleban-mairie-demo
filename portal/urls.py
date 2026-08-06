from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from . import pdf_reports

urlpatterns = [
    path("", views.home, name="home"),
    path("connexion/", LoginView.as_view(template_name="portal/login.html"), name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("mon-espace/", views.my_space, name="my_space"),
    path("projets/", views.projects, name="projects"),
    path("actualites/", views.news, name="news"),
    path("pages/<slug:slug>/", views.page_detail, name="page_detail"),
    path("gbeleban-en-carte/", views.map_public, name="map_public"),
    path("api/couches/<int:layer_id>.geojson", views.layer_geojson, name="layer_geojson"),
    path("urbanisme/", views.urbanism, name="urbanism"),
    path("api/cadastre.geojson", views.parcels_geojson, name="parcels_geojson"),
    path("api/cadastre/recherche/", views.parcel_search, name="parcel_search"),
    path("collecte-municipale/", views.municipal_collection, name="municipal_collection"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/export-pdf/", pdf_reports.dashboard_pdf, name="dashboard_pdf"),
    path("gestion/", views.management_home, name="management_home"),
    path("gestion/sig/import/", views.import_geojson_view, name="import_geojson"),
    path("gestion/cadastre/import/", views.import_cadastre_view, name="import_cadastre"),
]
