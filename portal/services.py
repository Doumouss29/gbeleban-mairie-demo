import json
from decimal import Decimal, InvalidOperation
from django.core.management import call_command
from django.db import transaction
from .models import MapLayer, MapFeature, UrbanismLayer, Parcel


def _load_geojson(uploaded):
    try:
        raw = uploaded.read().decode("utf-8-sig")
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"GeoJSON invalide : {exc}")
    if data.get("type") != "FeatureCollection":
        raise ValueError("Le fichier doit être un FeatureCollection GeoJSON.")
    return data


def _detect_fields(data):
    fields = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        for key in props.keys():
            if key not in fields:
                fields.append(key)
    return fields


def import_layer(uploaded, name, category="", color="#ef7d00", is_public=True, is_default_visible=True, display_fields=None):
    data = _load_geojson(uploaded)
    detected_fields = _detect_fields(data)
    selected_fields = [f for f in (display_fields or []) if f in detected_fields]
    if not selected_fields:
        selected_fields = detected_fields[:12]

    with transaction.atomic():
        layer = MapLayer.objects.create(
            name=name,
            category=category,
            color=color,
            is_public=is_public,
            is_default_visible=is_default_visible,
            display_fields=selected_fields,
        )
        objects = []
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            geom = feature.get("geometry") or {}
            if geom:
                objects.append(MapFeature(layer=layer, properties=props, geometry=geom))
        if objects:
            MapFeature.objects.bulk_create(objects, batch_size=1000)
    return layer


def import_cadastre(uploaded, fields):
    data = _load_geojson(uploaded)
    layer_name = (fields.get("layer_name") or "Cadastre Gbéléban").strip()
    replace_existing = bool(fields.get("replace_existing"))
    detected_fields = _detect_fields(data)
    selected_fields = [f for f in (fields.get("display_fields") or []) if f in detected_fields]
    if not selected_fields:
        selected_fields = detected_fields[:12]

    ref_key = fields.get("reference_field") or ("id_auto" if "id_auto" in detected_fields else "reference")
    ilot_key = fields.get("ilot_field") or ("ILOT" if "ILOT" in detected_fields else "")
    lot_key = fields.get("lot_field") or ("LOT" if "LOT" in detected_fields else "")
    area_key = fields.get("area_field") or ("SUPERFICIE" if "SUPERFICIE" in detected_fields else "")
    usage_key = fields.get("usage_field") or ("AFFECTATION" if "AFFECTATION" in detected_fields else "")
    section_key = fields.get("section_field") or ""
    parcel_key = fields.get("parcel_field") or ""

    def prop_value(props, key):
        value = props.get(key, "") if key else ""
        return "" if value is None else str(value).strip()

    objects = []
    refs = []
    seen_refs = set()
    for idx, feature in enumerate(data.get("features", []), 1):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        if not geom:
            continue

        raw_ref = props.get(ref_key)
        if ref_key == "id_auto":
            if raw_ref in (None, ""):
                # Le fichier contient quelques entités sans id_auto. Utiliser simplement
                # l'index de la ligne peut entrer en collision avec un vrai id_auto
                # (ex. GBL-1288). On réserve donc un préfixe distinct.
                reference = f"GBL-AUTO-{idx}"
            else:
                reference = f"GBL-{str(raw_ref).strip()}"
        else:
            reference = str(raw_ref if raw_ref not in (None, "") else f"AUTO-{idx}").strip()

        # Sécurité supplémentaire : aucune référence du fichier ne doit provoquer
        # une violation de la contrainte (source_layer, reference).
        if reference in seen_refs:
            base_reference = reference
            suffix = 2
            while reference in seen_refs:
                reference = f"{base_reference}-{suffix}"
                suffix += 1
        seen_refs.add(reference)
        refs.append(reference)

        area = None
        if area_key and props.get(area_key) not in (None, ""):
            try:
                area = Decimal(str(props.get(area_key)))
            except (InvalidOperation, ValueError):
                area = None

        objects.append(Parcel(
            source_layer=layer_name,
            reference=reference,
            section=prop_value(props, section_key),
            ilot=prop_value(props, ilot_key),
            lot=prop_value(props, lot_key),
            parcel_number=prop_value(props, parcel_key),
            area_m2=area,
            usage=prop_value(props, usage_key),
            properties=props,
            geometry=geom,
        ))

    if not objects:
        raise ValueError("Le GeoJSON ne contient aucune parcelle exploitable.")

    existing = set()
    if not replace_existing:
        existing = set(Parcel.objects.filter(source_layer=layer_name, reference__in=refs).values_list("reference", flat=True))
    created = len(objects) if replace_existing else sum(1 for r in refs if r not in existing)
    updated = 0 if replace_existing else len(refs) - created

    with transaction.atomic():
        if replace_existing:
            try:
                from .registry_models import ParcelOwnership
                ParcelOwnership.objects.all().delete()
            except Exception:
                pass
            Parcel.objects.all().delete()
            UrbanismLayer.objects.all().delete()

        UrbanismLayer.objects.update_or_create(
            name=layer_name,
            defaults={"display_fields": selected_fields},
        )

        if replace_existing:
            Parcel.objects.bulk_create(objects, batch_size=500)
        else:
            Parcel.objects.bulk_create(
                objects,
                batch_size=500,
                update_conflicts=True,
                unique_fields=["source_layer", "reference"],
                update_fields=["section", "ilot", "lot", "parcel_number", "area_m2", "usage", "properties", "geometry"],
            )

    if replace_existing:
        # Reconstitue immédiatement le lien parcelle/propriétaire à partir du GUIDE GBELEBAN.
        call_command("seed_parcel_owners")

    return layer_name, created, updated, replace_existing
