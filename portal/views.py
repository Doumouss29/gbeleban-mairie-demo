import json
from decimal import Decimal
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from .forms import GeoJSONImportForm, CadastreImportForm
from .models import SiteSettings, Page, QuickLink, News, Project, MapLayer, UrbanismLayer, Parcel, Taxpayer, Tax, Payment
from .services import import_layer, import_cadastre

URBANISM_GROUP = "Accès Urbanisme"
DASHBOARD_GROUP = "Accès Dashboard"


def _has_group_access(user, group_name):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())


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
    return render(request, "portal/my_space.html", {
        "can_urbanism": can_urbanism,
        "can_dashboard": can_dashboard,
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
def dashboard(request):
    if not _has_group_access(request.user, DASHBOARD_GROUP):
        messages.error(request, "Votre compte n'a pas accès au Dashboard.")
        return redirect("my_space")
    due = Tax.objects.aggregate(total=Sum("amount_due"))["total"] or Decimal("0")
    paid = Payment.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    rate = float(paid / due * 100) if due else 0
    status_counts = {s: Tax.objects.filter(status=s).count() for s in ("paid","partial","unpaid")}
    return render(request, "portal/dashboard.html", {
        "amount_due":due, "amount_paid":paid, "amount_remaining":max(due-paid,0),
        "collection_rate":round(rate,1), "taxpayers_count":Taxpayer.objects.count(),
        "projects_count":Project.objects.filter(is_published=True).count(),
        "status_counts_json":json.dumps(status_counts),
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
