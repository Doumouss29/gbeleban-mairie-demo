import calendar
import json
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from .forms import GeoJSONImportForm, CadastreImportForm
from .models import (
    SiteSettings, Page, QuickLink, News, Project, MapLayer, UrbanismLayer, Parcel,
    Taxpayer, Tax, Payment, MunicipalRevenueTheme, MunicipalRevenueEntry,
)
from .services import import_layer, import_cadastre

URBANISM_GROUP = "Accès Urbanisme"
DASHBOARD_GROUP = "Accès Dashboard"
COLLECTION_GROUP = "Accès Collecte municipale"


def _has_group_access(user, group_name):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())


def _parse_date(value, fallback):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date() if value else fallback
    except (TypeError, ValueError):
        return fallback


def _period_count(start_date, end_date, frequency):
    if end_date < start_date:
        return 0
    if frequency == "daily":
        return (end_date - start_date).days + 1
    if frequency == "weekly":
        return ((end_date - start_date).days // 7) + 1
    if frequency == "monthly":
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    return 0


def home(request):
    return render(request, "portal/home.html", {
        "quick_links": QuickLink.objects.filter(is_active=True)[:8],
        "projects": Project.objects.filter(is_published=True)[:6],
        "news_items": News.objects.filter(is_published=True)[:3],
    })


def projects(request):
    return render(request, "portal/projects.html", {"projects": Project.objects.filter(is_published=True)})


def news(request):
    return render(request, "portal/news.html", {"news_items": News.objects.filter(is_published=True)})


def page_detail(request, slug):
    if slug == "la-commune":
        return render(request, "portal/commune.html")
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "portal/page_detail.html", {"page": page})


def map_public(request):
    layers = MapLayer.objects.filter(is_public=True)
    return render(request, "portal/map.html", {"layers": layers})


def layer_geojson(request, layer_id):
    layer = get_object_or_404(MapLayer, pk=layer_id)
    if not layer.is_public and not request.user.is_authenticated:
        raise Http404
    features = [{"type":"Feature", "geometry":f.geometry, "properties":f.properties} for f in layer.features.all()]
    return JsonResponse({"type":"FeatureCollection", "features":features, "display_fields": layer.display_fields})


@login_required
def my_space(request):
    can_urbanism = _has_group_access(request.user, URBANISM_GROUP)
    can_dashboard = _has_group_access(request.user, DASHBOARD_GROUP)
    can_collection = _has_group_access(request.user, COLLECTION_GROUP)
    return render(request, "portal/my_space.html", {
        "can_urbanism": can_urbanism,
        "can_dashboard": can_dashboard,
        "can_collection": can_collection,
    })


@login_required
def urbanism(request):
    if not _has_group_access(request.user, URBANISM_GROUP):
        messages.error(request, "Votre compte n'a pas accès à l'espace Urbanisme.")
        return redirect("my_space")
    urban_layers = list(
        Parcel.objects.exclude(source_layer="")
        .values_list("source_layer", flat=True)
        .distinct()
        .order_by("source_layer")
    )
    return render(request, "portal/urbanism.html", {"urban_layers": urban_layers})


@login_required
def parcels_geojson(request):
    if not _has_group_access(request.user, URBANISM_GROUP):
        return JsonResponse({"detail": "Accès refusé"}, status=403)
    qs = Parcel.objects.all()
    layer_name = request.GET.get("layer", "").strip()
    if layer_name:
        qs = qs.filter(source_layer__iexact=layer_name)
    layer_meta = UrbanismLayer.objects.filter(name__iexact=layer_name).first() if layer_name else None
    display_fields = layer_meta.display_fields if layer_meta else []
    features = []
    for p in qs:
        props = dict(p.properties or {})
        props.update({
            "id": p.id,
            "couche": p.source_layer,
            "reference": p.reference,
            "section": p.section,
            "ilot": p.ilot,
            "lot": p.lot,
            "parcelle": p.parcel_number,
            "superficie": float(p.area_m2) if p.area_m2 is not None else None,
            "usage": p.usage,
        })
        features.append({"type":"Feature", "geometry":p.geometry, "properties":props})
    return JsonResponse({"type":"FeatureCollection", "features":features, "display_fields": display_fields})


@login_required
def parcel_search(request):
    if not _has_group_access(request.user, URBANISM_GROUP):
        return JsonResponse({"detail": "Accès refusé"}, status=403)
    qs = Parcel.objects.all()
    layer_name = request.GET.get("layer", "").strip()
    if layer_name:
        qs = qs.filter(source_layer__iexact=layer_name)
    for field, param in (("section","section"),("ilot","ilot"),("lot","lot"),("parcel_number","parcelle")):
        value = request.GET.get(param, "").strip()
        if value:
            qs = qs.filter(**{f"{field}__iexact": value})
    return JsonResponse({"results":[{
        "id":p.id,"couche":p.source_layer,"reference":p.reference,"section":p.section,
        "ilot":p.ilot,"lot":p.lot,"parcelle":p.parcel_number
    } for p in qs[:50]]})


@login_required
def municipal_collection(request):
    if not _has_group_access(request.user, COLLECTION_GROUP):
        messages.error(request, "Votre compte n'a pas accès à la Collecte municipale.")
        return redirect("my_space")

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "save_theme":
            theme_id = request.POST.get("theme_id")
            name = request.POST.get("name", "").strip()
            frequency = request.POST.get("frequency", "daily")
            description = request.POST.get("description", "").strip()
            target_raw = request.POST.get("target_amount", "").strip()
            is_active = request.POST.get("is_active") == "on"

            if not name:
                messages.error(request, "Le nom de la thématique est obligatoire.")
                return redirect("municipal_collection")
            if frequency not in dict(MunicipalRevenueTheme.FREQUENCY_CHOICES):
                messages.error(request, "La périodicité sélectionnée est invalide.")
                return redirect("municipal_collection")
            try:
                target_amount = Decimal(target_raw) if target_raw else None
                if target_amount is not None and target_amount < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                messages.error(request, "L'objectif doit être un montant positif.")
                return redirect("municipal_collection")

            if theme_id:
                theme = get_object_or_404(MunicipalRevenueTheme, pk=theme_id)
                if MunicipalRevenueTheme.objects.exclude(pk=theme.pk).filter(name__iexact=name).exists():
                    messages.error(request, "Une thématique portant ce nom existe déjà.")
                    return redirect("municipal_collection")
                theme.name = name
                theme.frequency = frequency
                theme.description = description
                theme.target_amount = target_amount
                theme.is_active = is_active
                theme.save()
                messages.success(request, f"Thématique « {theme.name} » mise à jour.")
            else:
                if MunicipalRevenueTheme.objects.filter(name__iexact=name).exists():
                    messages.error(request, "Une thématique portant ce nom existe déjà.")
                    return redirect("municipal_collection")
                MunicipalRevenueTheme.objects.create(
                    name=name,
                    frequency=frequency,
                    description=description,
                    target_amount=target_amount,
                    is_active=is_active,
                    created_by=request.user,
                )
                messages.success(request, f"Thématique « {name} » créée.")
            return redirect("municipal_collection")

        if action == "add_entry":
            theme = get_object_or_404(MunicipalRevenueTheme, pk=request.POST.get("theme_id"), is_active=True)
            collection_date = _parse_date(request.POST.get("collection_date"), None)
            amount_raw = request.POST.get("amount", "").strip()
            if not collection_date:
                messages.error(request, "La date de collecte est obligatoire.")
                return redirect("municipal_collection")
            try:
                amount = Decimal(amount_raw)
                if amount <= 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                messages.error(request, "Le montant collecté doit être supérieur à zéro.")
                return redirect("municipal_collection")
            MunicipalRevenueEntry.objects.create(
                theme=theme,
                collection_date=collection_date,
                amount=amount,
                comment=request.POST.get("comment", "").strip(),
                receipt_reference=request.POST.get("receipt_reference", "").strip(),
                entered_by=request.user,
            )
            messages.success(request, f"Collecte de {amount:,.0f} FCFA enregistrée pour « {theme.name} ».")
            return redirect("municipal_collection")

        if action == "delete_entry":
            entry = get_object_or_404(MunicipalRevenueEntry, pk=request.POST.get("entry_id"))
            entry.delete()
            messages.success(request, "Ligne de collecte supprimée.")
            return redirect("municipal_collection")

    themes = MunicipalRevenueTheme.objects.all()
    recent_entries = MunicipalRevenueEntry.objects.select_related("theme", "entered_by")[:60]
    month_start = date.today().replace(day=1)
    month_total = MunicipalRevenueEntry.objects.filter(collection_date__gte=month_start).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    today_total = MunicipalRevenueEntry.objects.filter(collection_date=date.today()).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return render(request, "portal/municipal_collection.html", {
        "themes": themes,
        "active_themes": themes.filter(is_active=True),
        "recent_entries": recent_entries,
        "today": date.today(),
        "today_total": today_total,
        "month_total": month_total,
    })


@login_required
def dashboard(request):
    if not _has_group_access(request.user, DASHBOARD_GROUP):
        messages.error(request, "Votre compte n'a pas accès au Dashboard.")
        return redirect("my_space")

    today = date.today()
    default_start = today.replace(day=1)
    default_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    start_date = _parse_date(request.GET.get("start"), default_start)
    end_date = _parse_date(request.GET.get("end"), default_end)
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    selected_theme = request.GET.get("theme", "").strip()
    entries = MunicipalRevenueEntry.objects.select_related("theme").filter(collection_date__range=(start_date, end_date))
    themes = MunicipalRevenueTheme.objects.all()
    target_themes = themes.filter(is_active=True)
    if selected_theme:
        entries = entries.filter(theme_id=selected_theme)
        target_themes = target_themes.filter(id=selected_theme)

    collected = entries.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    objective = Decimal("0")
    for theme in target_themes:
        if theme.target_amount:
            objective += theme.target_amount * _period_count(start_date, end_date, theme.frequency)
    remaining = max(objective - collected, Decimal("0")) if objective else Decimal("0")
    collection_rate = float(collected / objective * 100) if objective else 0

    by_theme = list(entries.values("theme__name").annotate(total=Sum("amount")).order_by("theme__name"))
    by_date = list(entries.values("collection_date").annotate(total=Sum("amount")).order_by("collection_date"))

    return render(request, "portal/dashboard.html", {
        "amount_due": objective,
        "amount_paid": collected,
        "amount_remaining": remaining,
        "collection_rate": round(collection_rate, 1),
        "entries_count": entries.count(),
        "active_themes_count": target_themes.count(),
        "projects_count": Project.objects.filter(is_published=True).count(),
        "themes": themes,
        "selected_theme": selected_theme,
        "start_date": start_date,
        "end_date": end_date,
        "theme_labels_json": json.dumps([row["theme__name"] for row in by_theme]),
        "theme_values_json": json.dumps([float(row["total"]) for row in by_theme]),
        "date_labels_json": json.dumps([row["collection_date"].strftime("%d/%m") for row in by_date]),
        "date_values_json": json.dumps([float(row["total"]) for row in by_date]),
    })


@staff_member_required
def management_home(request):
    return render(request, "portal/management.html", {"layer_count":MapLayer.objects.count(),"parcel_count":Parcel.objects.count(),"project_count":Project.objects.count()})


@staff_member_required
def import_geojson_view(request):
    form = GeoJSONImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            layer = import_layer(
                form.cleaned_data["geojson_file"],
                form.cleaned_data["layer_name"],
                form.cleaned_data["category"],
                form.cleaned_data["color"],
                form.cleaned_data["is_public"],
                form.cleaned_data["is_default_visible"],
                form.cleaned_data["display_fields"],
            )
            messages.success(request, f"Couche « {layer.name} » importée : {layer.features.count()} objet(s). Champs affichés : {', '.join(layer.display_fields) or 'aucun'}.")
            return redirect("management_home")
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, "portal/import_geojson.html", {"form":form})


@staff_member_required
def import_cadastre_view(request):
    form = CadastreImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            layer_name, created, updated = import_cadastre(form.cleaned_data["geojson_file"], form.cleaned_data)
            messages.success(request, f"Couche Urbanisme « {layer_name} » importée : {created} créée(s), {updated} mise(s) à jour.")
            return redirect("management_home")
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, "portal/import_cadastre.html", {"form":form})
