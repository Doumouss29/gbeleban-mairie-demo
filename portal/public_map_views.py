from django.http import JsonResponse
from django.shortcuts import render

from .public_map_data import get_public_map_geojson


def map_public(request):
    return render(request, "portal/map_search.html")


def public_map_geojson(request):
    return JsonResponse(get_public_map_geojson())
