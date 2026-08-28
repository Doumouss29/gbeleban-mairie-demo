from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

from .addressing import ADDRESS_LAYER, _address_payload, _address_props, _address_queryset


def _filtered(q="", status="", quality="", street=""):
    qs = _address_queryset()
    if q:
        qs = qs.filter(
            Q(properties__CODE_ADRESSE__icontains=q)
            | Q(properties__LIBELLE_ADR__icontains=q)
            | Q(properties__CODE_VOIE__icontains=q)
            | Q(properties__NOM_VOIE__icontains=q)
            | Q(properties__NOM_OFFICIEL__icontains=q)
            | Q(properties__TYPE_VOIE__icontains=q)
            | Q(properties__AFFECTATION__icontains=q)
            | Q(ilot__icontains=q)
            | Q(lot__icontains=q)
        )
    if status:
        qs = qs.filter(properties__STATUT_ADR=status)
    if quality:
        qs = qs.filter(properties__QUALITE_ADR=quality)
    if street:
        qs = qs.filter(properties__CODE_VOIE=street)
    return qs


def _street_options():
    """Return one normalized street record per technical street code."""
    options = {}
    rows = (
        _address_queryset()
        .exclude(properties__CODE_VOIE__isnull=True)
        .exclude(properties__CODE_VOIE="")
        .values_list("properties", flat=True)
    )
    for props in rows.iterator():
        props = dict(props or {})
        code = str(props.get("CODE_VOIE") or "").strip()
        if not code:
            continue
        official = str(props.get("NOM_OFFICIEL") or "").strip()
        road_type = str(props.get("TYPE_VOIE") or "").strip()
        current = options.get(code)
        # Prefer the record that already has an official name.
        if current is None or (official and not current["official_name"]):
            label_parts = [road_type, official] if official else [road_type, code]
            label = " ".join(x for x in label_parts if x).strip() or code
            options[code] = {
                "code": code,
                "official_name": official,
                "type": road_type,
                "label": label,
            }
    return sorted(options.values(), key=lambda x: x["code"])


def _post_queryset(request):
    q = request.POST.get("q", "").strip()
    status = request.POST.get("status", "").strip()
    quality = request.POST.get("quality", "").strip()
    street = request.POST.get("street", "").strip()
    if request.POST.get("all_filtered") == "1":
        return _filtered(q, status, quality, street)
    ids = [int(x) for x in request.POST.getlist("address_ids") if x.isdigit()]
    return _address_queryset().filter(id__in=ids)


def _return_url(request):
    parts = []
    for key in ("q", "status", "quality", "street", "page_size", "page"):
        value = request.POST.get(key, "").strip()
        if value:
            from urllib.parse import quote_plus
            parts.append(f"{key}={quote_plus(value)}")
    return "/gestion/adressage/" + ("?" + "&".join(parts) if parts else "")


@staff_member_required
def addressing_management_v2(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    quality = request.GET.get("quality", "").strip()
    street = request.GET.get("street", "").strip()
    try:
        page_size = int(request.GET.get("page_size", "100"))
    except (TypeError, ValueError):
        page_size = 100
    if page_size not in {50, 100, 250, 500}:
        page_size = 100

    qs = _filtered(q, status, quality, street).order_by("properties__CODE_VOIE", "properties__NUM_ADRESSE", "id")
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    rows = [_address_payload(p) for p in page_obj.object_list]

    street_options = _street_options()
    streets = [item["code"] for item in street_options]
    counts = {
        "total": _address_queryset().count(),
        "proposed": _address_queryset().filter(properties__STATUT_ADR="PROPOSEE").count(),
        "validated": _address_queryset().filter(properties__STATUT_ADR="VALIDEE").count(),
        "published": _address_queryset().filter(properties__STATUT_ADR="PUBLIEE").count(),
        "control": _address_queryset().filter(properties__QUALITE_ADR__in=["A_CONTROLER", "A_CONTROLER_PRIORITAIRE"]).count(),
    }
    querystring = request.GET.copy()
    querystring.pop("page", None)
    page_numbers = list(paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1))

    return render(request, "portal/addressing_management_v2.html", {
        "rows": rows,
        "page_obj": page_obj,
        "paginator": paginator,
        "page_numbers": page_numbers,
        "page_size": page_size,
        "querystring": querystring.urlencode(),
        "filtered_count": paginator.count,
        "counts": counts,
        "query": q,
        "status": status,
        "quality": quality,
        "street": street,
        "streets": streets,
        "street_options": street_options,
    })


@staff_member_required
def addressing_management_geojson_v2(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    quality = request.GET.get("quality", "").strip()
    street = request.GET.get("street", "").strip()
    features = []
    for parcel in _filtered(q, status, quality, street).only("id", "reference", "ilot", "lot", "properties", "geometry"):
        props = _address_payload(parcel)
        props["reference"] = parcel.reference
        features.append({"type": "Feature", "geometry": parcel.geometry, "properties": props})
    return JsonResponse({"type": "FeatureCollection", "features": features})


@staff_member_required
def addressing_bulk_status_v2(request):
    if request.method != "POST":
        raise Http404
    target = request.POST.get("target", "")
    if target not in {"VALIDEE", "PUBLIEE", "PROPOSEE"}:
        messages.error(request, "Statut invalide.")
        return redirect("addressing_management")
    qs = _post_queryset(request)
    updated = 0
    for parcel in qs.iterator():
        props = _address_props(parcel)
        props["STATUT_ADR"] = target
        history = list(props.get("HISTORIQUE_ADR") or [])
        history.append({"date": datetime.utcnow().isoformat(timespec="seconds") + "Z", "user": request.user.get_username(), "action": f"STATUT->{target}"})
        props["HISTORIQUE_ADR"] = history[-100:]
        parcel.properties = props
        parcel.save(update_fields=["properties"])
        updated += 1
    messages.success(request, f"{updated} adresse(s) passée(s) au statut {target}.")
    return redirect(_return_url(request))


@staff_member_required
def addressing_bulk_street_name(request):
    if request.method != "POST":
        raise Http404
    official_name = request.POST.get("official_name", "").strip()
    if not official_name:
        messages.error(request, "Saisissez le nouveau nom officiel de la rue.")
        return redirect(_return_url(request))
    qs = _post_queryset(request)
    if not qs.exists():
        messages.error(request, "Sélectionnez au moins une adresse.")
        return redirect(_return_url(request))

    updated = 0
    for parcel in qs.iterator():
        props = _address_props(parcel)
        before = props.get("NOM_OFFICIEL", "")
        props["NOM_OFFICIEL"] = official_name
        numero = str(props.get("NUM_ADRESSE") or "").strip()
        suffixe = str(props.get("SUFFIXE") or "").strip()
        numero_aff = f"{numero}{suffixe}".strip()
        type_voie = str(props.get("TYPE_VOIE") or "Rue").strip()
        props["LIBELLE_ADR"] = f"{numero_aff} {type_voie} {official_name}, Gbéléban".strip()
        history = list(props.get("HISTORIQUE_ADR") or [])
        history.append({
            "date": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "user": request.user.get_username(),
            "action": "NOM_RUE_MASSE",
            "avant": before,
            "apres": official_name,
        })
        props["HISTORIQUE_ADR"] = history[-100:]
        parcel.properties = props
        parcel.save(update_fields=["properties"])
        updated += 1
    messages.success(request, f"Nom officiel « {official_name} » appliqué à {updated} adresse(s).")
    return redirect(_return_url(request))


@staff_member_required
def addressing_delete_selected_v2(request):
    if request.method != "POST":
        raise Http404
    qs = _post_queryset(request)
    count = qs.count()
    qs.delete()
    messages.success(request, f"{count} adresse(s) supprimée(s).")
    return redirect(_return_url(request))
