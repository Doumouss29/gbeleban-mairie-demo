import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .addressing import ADDRESS_LAYER
from .models import Parcel


def _internal_results(query):
    qs = Parcel.objects.filter(
        source_layer=ADDRESS_LAYER,
        properties__STATUT_ADR="PUBLIEE",
    ).filter(
        Q(properties__CODE_ADRESSE__icontains=query)
        | Q(properties__LIBELLE_ADR__icontains=query)
        | Q(properties__CODE_VOIE__icontains=query)
        | Q(ilot__icontains=query)
        | Q(lot__icontains=query)
    ).order_by("properties__CODE_VOIE", "properties__NUM_ADRESSE")[:12]

    results = []
    for parcel in qs:
        props = dict(parcel.properties or {})
        lon = props.get("ADR_LON")
        lat = props.get("ADR_LAT")
        if lon in (None, "") or lat in (None, ""):
            continue
        try:
            lon = float(lon)
            lat = float(lat)
        except (TypeError, ValueError):
            continue
        results.append({
            "source": "gbeleban",
            "label": props.get("LIBELLE_ADR") or props.get("CODE_ADRESSE") or "Adresse de Gbéléban",
            "code": props.get("CODE_ADRESSE", ""),
            "longitude": lon,
            "latitude": lat,
            "ilot": parcel.ilot,
            "lot": parcel.lot,
        })
    return results


def _osm_results(query):
    params = urlencode({
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 8,
        "accept-language": "fr",
        "countrycodes": "ci",
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mairie-Gbeleban-AddressSearch/1.0 (https://mairie-gbeleban.ci)",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=7) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return [], "Recherche OpenStreetMap temporairement indisponible"

    results = []
    for item in data[:8]:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            continue
        results.append({
            "source": "osm",
            "label": item.get("display_name") or query,
            "osm_type": item.get("osm_type", ""),
            "osm_id": item.get("osm_id"),
            "longitude": lon,
            "latitude": lat,
        })
    return results, ""


@require_GET
def combined_address_search(request):
    query = request.GET.get("q", "").strip()
    external = request.GET.get("external", "1") == "1"
    if len(query) < 2:
        return JsonResponse({
            "query": query,
            "results": [],
            "osm_enabled": True,
        })

    internal = _internal_results(query)
    osm = []
    osm_message = ""
    if external:
        osm, osm_message = _osm_results(query)

    return JsonResponse({
        "query": query,
        "results": internal + osm,
        "internal_count": len(internal),
        "osm_count": len(osm),
        "osm_enabled": True,
        "osm_message": osm_message,
    })
