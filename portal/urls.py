from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from . import pdf_reports
from . import public_map_views
from . import parcel_registry_views
from . import news_views
from . import seo_views
from . import addressing
from . import addressing_delete

urlpatterns = [
    path("robots.txt", seo_views.robots_txt, name="robots_txt"),
    path("sitemap.xml", seo_views.sitemap_xml, name="sitemap_xml"),
    path("", views.home, name="home"),
    path("connexion/", LoginView.as_view(template_name="portal/login.html"), name="login"),
    path("deconnexion/", LogoutView.as_view(), name="logout"),
    path("mon-espace/", views.my_space, name="my_space"),
    path("projets/", views.projects, name="projects"),
    path("actualites/", views.news, name="news"),
    path("actualites/<int:news_id>/", news_views.news_detail, name="news_detail"),
    path("pages/<slug:slug>/", views.page_detail, name="page_detail"),
    path("gbeleban-en-carte/", public_map_views.map_public, name="map_public"),
    path("api/gbeleban-carte.geojson", public_map_views.public_map_geojson, name="public_map_geojson"),
    path("api/couches/<int:layer_id>.geojson", views.layer_geojson, name="layer_geojson"),
    path("adresses/", addressing.address_search, name="address_search"),
    path("adresses/<str:code>/", addressing.address_detail, name="address_detail"),
    path("api/adresses.geojson", addressing.address_points_geojson, name="address_points_geojson"),
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
    path("gestion/adressage/", addressing.addressing_management, name="addressing_management"),
    path("gestion/adressage/import/", addressing.addressing_import, name="addressing_import"),
    path("gestion/adressage/statut/", addressing.addressing_bulk_status, name="addressing_bulk_status"),
    path("gestion/adressage/supprimer-selection/", addressing_delete.delete_selected_addresses, name="addressing_delete_selected"),
    path("gestion/adressage/<int:parcel_id>/modifier/", addressing.addressing_edit, name="addressing_edit"),
    path("gestion/adressage/<int:parcel_id>/supprimer/", addressing_delete.delete_address, name="addressing_delete"),
]
