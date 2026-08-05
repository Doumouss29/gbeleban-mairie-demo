import json
from decimal import Decimal, InvalidOperation
from .models import MapLayer, MapFeature, Parcel


def _load_geojson(uploaded):
    try:
        raw = uploaded.read().decode("utf-8-sig")
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"GeoJSON invalide : {exc}")
    if data.get("type") != "FeatureCollection":
        raise ValueError("Le fichier doit être un FeatureCollection GeoJSON.")
    return data


def import_layer(uploaded, name, category="", color="#ef7d00", is_public=True, is_default_visible=True):
    data = _load_geojson(uploaded)
    layer = MapLayer.objects.create(
        name=name,
        category=category,
        color=color,
        is_public=is_public,
        is_default_visible=is_default_visible,
    )
    fields = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        if geom:
            MapFeature.objects.create(layer=layer, properties=props, geometry=geom)
        for key in props:
            if key not in fields and len(fields) < 12:
                fields.append(key)
    layer.display_fields = fields
    layer.save(update_fields=["display_fields"])
    return layer


def import_cadastre(uploaded, fields):
    data = _load_geojson(uploaded)
    layer_name = (fields.get("layer_name") or "Parcelles cadastrales").strip()
    created = updated = 0
    for idx, feature in enumerate(data.get("features", []), 1):
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        ref_key = fields.get("reference_field") or "reference"
        reference = str(props.get(ref_key) or f"IMPORT-{idx}")

        def val(form_key):
            key = fields.get(form_key)
            return str(props.get(key, "")) if key else ""

        area = None
        area_key = fields.get("area_field")
        if area_key and props.get(area_key) not in (None, ""):
            try:
                area = Decimal(str(props.get(area_key)))
            except InvalidOperation:
                area = None

        _, was_created = Parcel.objects.update_or_create(
            source_layer=layer_name,
            reference=reference,
            defaults={
                "section": val("section_field"),
                "ilot": val("ilot_field"),
                "lot": val("lot_field"),
                "parcel_number": val("parcel_field"),
                "area_m2": area,
                "usage": val("usage_field"),
                "geometry": geom,
            },
        )
        created += int(was_created)
        updated += int(not was_created)
    return layer_name, created, updated
