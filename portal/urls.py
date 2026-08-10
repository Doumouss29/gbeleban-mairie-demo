from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from . import pdf_reports
from . import public_map_views
from . import parcel_registry_views

urlpatterns = [
    path("", views.home, name="home"),
    path("connexion/", LoginView.as_view(template_name="portal/login.html"), name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("mon-espace/", views.my_space, name="my_space"),
    path("projets/", views.projects, name="projects"),
    path("actualites/", views.news, name="news"),
    path("pages/<slug:slug>/", views.page_detail, name="page_detail"),
    path("gbeleban-en-carte/", public_map_views.map_public, name="map_public"),
    path("api/gbeleban-carte.geojson", public_map_views.public_map_geojson, name="public_map_geojson"),
    path("api/couches/<int:layer_id>.geojson", views.layer_geojson, name="layer_geojson"),
    path("urbanisme/", views.urbanism, name="urbanism"),
    path("api/cadastre.geojson", views.parcels_geojson, name="parcels_geojson"),
    path("api/cadastre/recherche/", views.parcel_search, name="parcel_search"),
    path("api/cadastre/parcelles/<int:parcel_id>/fiche/", parcel_registry_views.parcel_record, name="parcel_record"),
    path("api/cadastre/parcelles/<int:parcel_id>/proprietaires/", parcel_registry_views.parcel_add_owner, name="parcel_add_owner"),
    path("api/cadastre/proprietaires/<int:owner_id>/modifier/", parcel_registry_views.parcel_owner_update, name="parcel_owner_update"),
    path("api/cadastre/proprietaires/<int:owner_id>/piece/", parcel_registry_views.parcel_owner_identity, name="parcel_owner_identity"),
    path("api/cadastre/historique/<int:ownership_id>/modifier/", parcel_registry_views.parcel_ownership_update, name="parcel_ownership_update"),
    path("collecte-municipale/", views.municipal_collection, name="municipal_collection"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/export-pdf/", pdf_reports.dashboard_pdf, name="dashboard_pdf"),
    path("gestion/", views.management_home, name="management_home"),
    path("gestion/sig/import/", views.import_geojson_view, name="import_geojson"),
    path("gestion/cadastre/import/", views.import_cadastre_view, name="import_cadastre"),
]
