import json
from decimal import Decimal, InvalidOperation
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
    layer_name = (fields.get("layer_name") or "Parcelles cadastrales").strip()
    detected_fields = _detect_fields(data)
    selected_fields = [f for f in (fields.get("display_fields") or []) if f in detected_fields]
    if not selected_fields:
        selected_fields = detected_fields[:12]

    refs = []
    objects = []
    ref_key = fields.get("reference_field") or "reference"

    def prop_value(props, form_key):
        key = fields.get(form_key)
        value = props.get(key, "") if key else ""
        return "" if value is None else str(value)

    for idx, feature in enumerate(data.get("features", []), 1):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        reference = str(props.get(ref_key) or f"IMPORT-{idx}")
        refs.append(reference)

        area = None
        area_key = fields.get("area_field")
        if area_key and props.get(area_key) not in (None, ""):
            try:
                area = Decimal(str(props.get(area_key)))
            except InvalidOperation:
                area = None

        objects.append(Parcel(
            source_layer=layer_name,
            reference=reference,
            section=prop_value(props, "section_field"),
            ilot=prop_value(props, "ilot_field"),
            lot=prop_value(props, "lot_field"),
            parcel_number=prop_value(props, "parcel_field"),
            area_m2=area,
            usage=prop_value(props, "usage_field"),
            properties=props,
            geometry=geom,
        ))

    existing = set(Parcel.objects.filter(source_layer=layer_name, reference__in=refs).values_list("reference", flat=True))
    created = sum(1 for r in refs if r not in existing)
    updated = len(refs) - created

    with transaction.atomic():
        UrbanismLayer.objects.update_or_create(
            name=layer_name,
            defaults={"display_fields": selected_fields},
        )
        if objects:
            Parcel.objects.bulk_create(
                objects,
                batch_size=500,
                update_conflicts=True,
                unique_fields=["source_layer", "reference"],
                update_fields=["section", "ilot", "lot", "parcel_number", "area_m2", "usage", "properties", "geometry"],
            )

    return layer_name, created, updated
