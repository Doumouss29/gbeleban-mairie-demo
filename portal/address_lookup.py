import json
import os
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


def _google_results(query):
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return [], False, "Clé Google Maps non configurée"

    params = urlencode({
        "address": query,
        "key": api_key,
        "language": "fr",
        "region": "ci",
    })
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
    req = Request(url, headers={"User-Agent": "Mairie-Gbeleban/1.0"})

    try:
        with urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return [], True, "Recherche Google temporairement indisponible"

    status = data.get("status")
    if status not in {"OK", "ZERO_RESULTS"}:
        return [], True, f"Google Maps : {status or 'erreur'}"

    results = []
    for item in data.get("results", [])[:8]:
        loc = ((item.get("geometry") or {}).get("location") or {})
        lat = loc.get("lat")
        lon = loc.get("lng")
        if lat is None or lon is None:
            continue
        results.append({
            "source": "google",
            "label": item.get("formatted_address") or query,
            "place_id": item.get("place_id", ""),
            "longitude": float(lon),
            "latitude": float(lat),
        })
    return results, True, ""


@require_GET
def combined_address_search(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"query": query, "results": [], "google_enabled": bool(os.environ.get("GOOGLE_MAPS_API_KEY"))})

    internal = _internal_results(query)
    google, google_enabled, google_message = _google_results(query)

    return JsonResponse({
        "query": query,
        "results": internal + google,
        "internal_count": len(internal),
        "google_count": len(google),
        "google_enabled": google_enabled,
        "google_message": google_message,
    })
