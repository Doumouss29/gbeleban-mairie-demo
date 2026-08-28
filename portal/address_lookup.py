import json
import re
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .addressing import ADDRESS_LAYER
from .models import Parcel


def _normalize(value):
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _internal_results(query, include_unpublished=False):
    qs = Parcel.objects.filter(source_layer=ADDRESS_LAYER)
    if not include_unpublished:
        qs = qs.filter(properties__STATUT_ADR="PUBLIEE")

    qs = qs.filter(
        Q(properties__CODE_ADRESSE__icontains=query)
        | Q(properties__LIBELLE_ADR__icontains=query)
        | Q(properties__CODE_VOIE__icontains=query)
        | Q(properties__NOM_VOIE__icontains=query)
        | Q(properties__NOM_OFFICIEL__icontains=query)
        | Q(properties__AFFECTATION__icontains=query)
        | Q(properties__GROUPE__icontains=query)
        | Q(ilot__icontains=query)
        | Q(lot__icontains=query)
    ).order_by("properties__CODE_VOIE", "properties__NUM_ADRESSE")[:18]

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

        parcel_name = str(props.get("AFFECTATION") or "").strip()
        address_label = str(props.get("LIBELLE_ADR") or props.get("CODE_ADRESSE") or "Adresse de Gbéléban").strip()
        label = f"{parcel_name} — {address_label}" if parcel_name else address_label

        results.append({
            "source": "gbeleban",
            "label": label,
            "address_label": address_label,
            "parcel_name": parcel_name,
            "code": props.get("CODE_ADRESSE", ""),
            "longitude": lon,
            "latitude": lat,
            "ilot": parcel.ilot,
            "lot": parcel.lot,
            "statut": props.get("STATUT_ADR", ""),
            "parcel_id": parcel.id,
        })
    return results


def _osm_results(query):
    params = urlencode({
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 10,
        "accept-language": "fr",
        "dedupe": 1,
    })
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mairie-Gbeleban-AddressSearch/1.2 (https://mairie-gbeleban.ci)",
            "Accept": "application/json",
            "Referer": "https://mairie-gbeleban.ci/",
        },
    )

    try:
        with urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return [], "Recherche OpenStreetMap temporairement indisponible"

    results = []
    seen = set()
    for item in data:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            continue

        label = item.get("display_name") or query
        first_name = _normalize(label.split(",", 1)[0])
        # Nominatim peut renvoyer plusieurs objets administratifs pour une même ville.
        # On fusionne les résultats de même nom situés pratiquement au même endroit.
        geo_key = (first_name, round(lat, 2), round(lon, 2))
        if geo_key in seen:
            continue
        seen.add(geo_key)

        results.append({
            "source": "osm",
            "label": label,
            "osm_type": item.get("osm_type", ""),
            "osm_id": item.get("osm_id"),
            "longitude": lon,
            "latitude": lat,
        })
        if len(results) >= 6:
            break
    return results, ""


@require_GET
def combined_address_search(request):
    query = request.GET.get("q", "").strip()
    external = request.GET.get("external", "1") == "1"
    include_unpublished = request.GET.get("all", "0") == "1" and request.user.is_authenticated and request.user.is_staff
    if len(query) < 2:
        return JsonResponse({"query": query, "results": [], "osm_enabled": True})

    internal = _internal_results(query, include_unpublished=include_unpublished)
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
