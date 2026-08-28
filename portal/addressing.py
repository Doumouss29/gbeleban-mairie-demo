import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import MapFeature, MapLayer, Parcel, QuickLink

ADDRESS_LAYER = "Adressage Gbéléban"
ROAD_LAYER = "Axes de voirie - Adressage"
MANUAL_KEYS = ["NUM_ADRESSE", "SUFFIXE", "CODE_VOIE", "NOM_OFFICIEL", "LIBELLE_ADR", "CODE_ADRESSE", "STATUT_ADR", "ADR_LAT", "ADR_LON"]


def _address_queryset():
    return Parcel.objects.filter(source_layer=ADDRESS_LAYER)


def _address_props(parcel):
    return dict(parcel.properties or {})


def _address_payload(parcel):
    p = _address_props(parcel)
    return {
        "id": parcel.id,
        "code": p.get("CODE_ADRESSE", ""),
        "label": p.get("LIBELLE_ADR", ""),
        "numero": p.get("NUM_ADRESSE", ""),
        "suffixe": p.get("SUFFIXE", ""),
        "code_voie": p.get("CODE_VOIE", ""),
        "nom_officiel": p.get("NOM_OFFICIEL", ""),
        "type_voie": p.get("TYPE_VOIE", ""),
        "ilot": parcel.ilot,
        "lot": parcel.lot,
        "statut": p.get("STATUT_ADR", "PROPOSEE"),
        "qualite": p.get("QUALITE_ADR", ""),
        "latitude": p.get("ADR_LAT"),
        "longitude": p.get("ADR_LON"),
    }


def address_search(request):
    q = request.GET.get("q", "").strip()
    results = []
    if q:
        qs = _address_queryset().filter(properties__STATUT_ADR="PUBLIEE")
        qs = qs.filter(
            Q(properties__CODE_ADRESSE__icontains=q)
            | Q(properties__LIBELLE_ADR__icontains=q)
            | Q(properties__CODE_VOIE__icontains=q)
            | Q(ilot__icontains=q)
            | Q(lot__icontains=q)
        ).order_by("properties__CODE_VOIE", "properties__NUM_ADRESSE")[:40]
        results = [_address_payload(p) for p in qs]
    return render(request, "portal/address_search.html", {"query": q, "results": results})


def address_detail(request, code):
    parcel = get_object_or_404(
        _address_queryset(),
        properties__CODE_ADRESSE=code,
        properties__STATUT_ADR="PUBLIEE",
    )
    return render(request, "portal/address_detail.html", {"address": _address_payload(parcel)})


def address_points_geojson(request):
    features = []
    for parcel in _address_queryset().filter(properties__STATUT_ADR="PUBLIEE"):
        p = _address_props(parcel)
        lat = p.get("ADR_LAT")
        lon = p.get("ADR_LON")
        if lat in (None, "") or lon in (None, ""):
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
            "properties": _address_payload(parcel),
        })
    return JsonResponse({"type": "FeatureCollection", "features": features})


@staff_member_required
def addressing_management(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    quality = request.GET.get("quality", "").strip()
    qs = _address_queryset()
    if q:
        qs = qs.filter(
            Q(properties__CODE_ADRESSE__icontains=q)
            | Q(properties__LIBELLE_ADR__icontains=q)
            | Q(properties__CODE_VOIE__icontains=q)
            | Q(ilot__icontains=q)
            | Q(lot__icontains=q)
        )
    if status:
        qs = qs.filter(properties__STATUT_ADR=status)
    if quality:
        qs = qs.filter(properties__QUALITE_ADR=quality)

    rows = [_address_payload(p) for p in qs.order_by("properties__CODE_VOIE", "properties__NUM_ADRESSE")[:250]]
    counts = {
        "total": _address_queryset().count(),
        "proposed": _address_queryset().filter(properties__STATUT_ADR="PROPOSEE").count(),
        "validated": _address_queryset().filter(properties__STATUT_ADR="VALIDEE").count(),
        "published": _address_queryset().filter(properties__STATUT_ADR="PUBLIEE").count(),
        "control": _address_queryset().filter(properties__QUALITE_ADR__in=["A_CONTROLER", "A_CONTROLER_PRIORITAIRE"]).count(),
    }
    return render(request, "portal/addressing_management.html", {
        "rows": rows, "counts": counts, "query": q, "status": status, "quality": quality,
    })


@staff_member_required
def addressing_import(request):
    if request.method != "POST":
        return redirect("addressing_management")

    roads_file = request.FILES.get("roads_file")
    parcels_file = request.FILES.get("parcels_file")
    if not roads_file or not parcels_file:
        messages.error(request, "Sélectionnez les deux GeoJSON : axes de voirie et parcelles d'adressage.")
        return redirect("addressing_management")

    try:
        roads = json.loads(roads_file.read().decode("utf-8-sig"))
        parcels = json.loads(parcels_file.read().decode("utf-8-sig"))
    except Exception as exc:
        messages.error(request, f"GeoJSON invalide : {exc}")
        return redirect("addressing_management")

    if roads.get("type") != "FeatureCollection" or parcels.get("type") != "FeatureCollection":
        messages.error(request, "Les deux fichiers doivent être des FeatureCollection GeoJSON.")
        return redirect("addressing_management")

    road_layer, _ = MapLayer.objects.update_or_create(
        name=ROAD_LAYER,
        defaults={
            "category": "Adressage communal",
            "description": "Axes de voirie de référence pour l'adressage de Gbéléban.",
            "color": "#ef7d00",
            "is_public": False,
            "is_default_visible": False,
            "display_fields": ["CODE_VOIE", "NOM_OFFICIEL", "TYPE_VOIE", "LONGUEUR_M", "NB_ADRESSES"],
        },
    )
    road_layer.features.all().delete()
    road_features = []
    for feature in roads.get("features", []):
        if feature.get("geometry"):
            road_features.append(MapFeature(layer=road_layer, geometry=feature.get("geometry") or {}, properties=feature.get("properties") or {}))
    MapFeature.objects.bulk_create(road_features, batch_size=500)

    existing = {p.reference: p for p in _address_queryset()}
    seen = set()
    created = updated = preserved = 0
    for feature in parcels.get("features", []):
        incoming = dict(feature.get("properties") or {})
        reference = str(incoming.get("ID_PARCELLE") or incoming.get("id_auto") or "").strip()
        if not reference:
            continue
        seen.add(reference)
        obj = existing.get(reference)

        # Une correction municipale déjà effectuée ne doit jamais être écrasée
        # par une régénération QGIS. Les valeurs calculées restent conservées
        # dans CALCUL_AUTO pour comparaison/audit.
        if obj:
            current = _address_props(obj)
            has_manual_history = bool(current.get("HISTORIQUE_ADR"))
            if has_manual_history or current.get("STATUT_ADR") in {"VALIDEE", "PUBLIEE"}:
                incoming["CALCUL_AUTO"] = {k: incoming.get(k) for k in MANUAL_KEYS}
                for key in MANUAL_KEYS:
                    if key in current:
                        incoming[key] = current.get(key)
                if current.get("HISTORIQUE_ADR"):
                    incoming["HISTORIQUE_ADR"] = current.get("HISTORIQUE_ADR")
                preserved += 1

        defaults = {
            "section": str(incoming.get("SECTION") or ""),
            "ilot": str(incoming.get("ILOT") or ""),
            "lot": str(incoming.get("LOT") or ""),
            "parcel_number": str(incoming.get("PARCELLE") or ""),
            "usage": str(incoming.get("AFFECTATION") or ""),
            "properties": incoming,
            "geometry": feature.get("geometry") or {},
        }
        try:
            defaults["area_m2"] = Decimal(str(incoming.get("SUPERFICIE"))) if incoming.get("SUPERFICIE") not in (None, "") else None
        except (InvalidOperation, ValueError):
            defaults["area_m2"] = None

        if obj:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()
            updated += 1
        else:
            Parcel.objects.create(source_layer=ADDRESS_LAYER, reference=reference, **defaults)
            created += 1

    _address_queryset().exclude(reference__in=seen).delete()

    QuickLink.objects.update_or_create(
        url="/adresses/",
        defaults={
            "title": "Trouver une adresse",
            "description": "Rechercher une rue, un numéro, un îlot ou un lot à Gbéléban.",
            "icon": "📍",
            "is_active": True,
            "order": 15,
        },
    )

    messages.success(request, f"Adressage importé : {len(road_features)} axes, {created} adresse(s) créée(s), {updated} mise(s) à jour, {preserved} correction(s) municipale(s) préservée(s).")
    return redirect("addressing_management")


@staff_member_required
def addressing_edit(request, parcel_id):
    parcel = get_object_or_404(_address_queryset(), pk=parcel_id)
    if request.method == "POST":
        props = _address_props(parcel)
        before = {k: props.get(k) for k in MANUAL_KEYS}

        numero = request.POST.get("numero", "").strip()
        suffixe = request.POST.get("suffixe", "").strip().upper()
        code_voie = request.POST.get("code_voie", "").strip()
        nom_officiel = request.POST.get("nom_officiel", "").strip()
        statut = request.POST.get("statut", "PROPOSEE").strip()
        latitude = request.POST.get("latitude", "").strip()
        longitude = request.POST.get("longitude", "").strip()

        if not numero or not code_voie:
            messages.error(request, "Le numéro et le code voie sont obligatoires.")
            return redirect("addressing_edit", parcel_id=parcel.id)
        if statut not in {"PROPOSEE", "VALIDEE", "PUBLIEE"}:
            messages.error(request, "Statut invalide.")
            return redirect("addressing_edit", parcel_id=parcel.id)

        numero_aff = f"{numero}{suffixe}"
        new_code = f"GBL-{code_voie}-{numero_aff}"
        if _address_queryset().exclude(pk=parcel.pk).filter(properties__CODE_ADRESSE=new_code).exists():
            messages.error(request, f"Le code adresse {new_code} est déjà utilisé par une autre parcelle.")
            return redirect("addressing_edit", parcel_id=parcel.id)

        props["NUM_ADRESSE"] = numero
        props["SUFFIXE"] = suffixe
        props["CODE_VOIE"] = code_voie
        props["NOM_OFFICIEL"] = nom_officiel
        props["STATUT_ADR"] = statut
        props["ADR_LAT"] = latitude
        props["ADR_LON"] = longitude
        type_voie = str(props.get("TYPE_VOIE") or "Rue")
        voie_aff = nom_officiel or code_voie
        props["LIBELLE_ADR"] = f"{numero_aff} {type_voie} {voie_aff}, Gbéléban".strip()
        props["CODE_ADRESSE"] = new_code
        history = list(props.get("HISTORIQUE_ADR") or [])
        history.append({
            "date": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "user": request.user.get_username(),
            "avant": before,
            "apres": {k: props.get(k) for k in MANUAL_KEYS},
        })
        props["HISTORIQUE_ADR"] = history[-100:]
        parcel.properties = props
        parcel.save(update_fields=["properties"])
        messages.success(request, "Adresse mise à jour.")
        return redirect("addressing_management")

    return render(request, "portal/addressing_edit.html", {"parcel": parcel, "address": _address_payload(parcel), "props": _address_props(parcel)})


@staff_member_required
def addressing_bulk_status(request):
    if request.method != "POST":
        raise Http404
    target = request.POST.get("target", "")
    if target not in {"VALIDEE", "PUBLIEE", "PROPOSEE"}:
        messages.error(request, "Statut invalide.")
        return redirect("addressing_management")
    ids = [int(x) for x in request.POST.getlist("address_ids") if x.isdigit()]
    updated = 0
    for parcel in _address_queryset().filter(id__in=ids):
        props = _address_props(parcel)
        props["STATUT_ADR"] = target
        history = list(props.get("HISTORIQUE_ADR") or [])
        history.append({"date": datetime.utcnow().isoformat(timespec="seconds") + "Z", "user": request.user.get_username(), "action": f"STATUT->{target}"})
        props["HISTORIQUE_ADR"] = history[-100:]
        parcel.properties = props
        parcel.save(update_fields=["properties"])
        updated += 1
    messages.success(request, f"{updated} adresse(s) passée(s) au statut {target}.")
    return redirect("addressing_management")
