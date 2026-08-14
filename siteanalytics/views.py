import json
from datetime import date, datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractHour
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .middleware import visitor_hash
from .models import ClickEvent, PageVisit


PRIVATE_PREFIXES = (
    "/admin/", "/gestion/", "/connexion/", "/deconnexion/", "/mon-espace/",
    "/urbanisme/", "/dashboard/", "/collecte-municipale/", "/pilotage-projets/",
    "/api/", "/analytics/", "/static/",
)


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _range_from_request(request):
    today = timezone.localdate()
    period = request.GET.get("period", "month")
    if period == "day":
        start = end = today
    elif period == "week":
        start, end = today - timedelta(days=6), today
    elif period == "year":
        start, end = date(today.year, 1, 1), date(today.year, 12, 31)
    elif period == "custom":
        start = _parse_date(request.GET.get("start")) or today
        end = _parse_date(request.GET.get("end")) or start
        if end < start:
            start, end = end, start
    else:
        period = "month"
        start, end = today.replace(day=1), today
    return period, start, end


def _datetime_bounds(start, end):
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()), tz)
    end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), datetime.min.time()), tz)
    return start_dt, end_dt


@staff_member_required
def dashboard(request):
    period, start, end = _range_from_request(request)
    start_dt, end_dt = _datetime_bounds(start, end)
    visits = PageVisit.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)
    clicks = ClickEvent.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)

    page_views = visits.count()
    unique_visitors = visits.values("visitor_hash").distinct().count()
    clicks_count = clicks.count()

    top_pages = list(visits.values("path").annotate(total=Count("id")).order_by("-total", "path")[:12])
    top_clicks = list(clicks.values("target_path", "label").annotate(total=Count("id")).order_by("-total")[:12])
    countries = list(visits.exclude(country="").values("country").annotate(total=Count("visitor_hash", distinct=True)).order_by("-total")[:12])
    regions = list(visits.exclude(region="").values("country", "region").annotate(total=Count("visitor_hash", distinct=True)).order_by("-total")[:12])
    cities = list(visits.exclude(city="").values("country", "city").annotate(total=Count("visitor_hash", distinct=True)).order_by("-total")[:12])
    devices = list(visits.exclude(device="").values("device").annotate(total=Count("visitor_hash", distinct=True)).order_by("-total"))

    daily_rows = list(
        visits.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"), visitors=Count("visitor_hash", distinct=True))
        .order_by("day")
    )
    max_daily = max([row["total"] for row in daily_rows] or [1])
    for row in daily_rows:
        row["width"] = round(row["total"] / max_daily * 100, 1)

    hourly_rows = list(
        visits.annotate(hour=ExtractHour("created_at"))
        .values("hour")
        .annotate(total=Count("id"), visitors=Count("visitor_hash", distinct=True))
        .order_by("hour")
    )
    hourly_map = {row["hour"]: row for row in hourly_rows}
    hourly_rows = [
        {
            "hour": hour,
            "label": f"{hour:02d}h–{(hour + 1) % 24:02d}h",
            "total": hourly_map.get(hour, {}).get("total", 0),
            "visitors": hourly_map.get(hour, {}).get("visitors", 0),
        }
        for hour in range(24)
    ]
    max_hourly = max([row["total"] for row in hourly_rows] or [1])
    if max_hourly <= 0:
        max_hourly = 1
    for row in hourly_rows:
        row["width"] = round(row["total"] / max_hourly * 100, 1)

    recent_visits = list(
        visits.order_by("-created_at")
        .values("created_at", "path", "country", "region", "city", "device")[:100]
    )

    context = {
        "period": period,
        "start": start,
        "end": end,
        "page_views": page_views,
        "unique_visitors": unique_visitors,
        "clicks_count": clicks_count,
        "avg_pages": round(page_views / unique_visitors, 1) if unique_visitors else 0,
        "top_pages": top_pages,
        "top_clicks": top_clicks,
        "countries": countries,
        "regions": regions,
        "cities": cities,
        "devices": devices,
        "daily_rows": daily_rows,
        "hourly_rows": hourly_rows,
        "recent_visits": recent_visits,
    }
    return render(request, "siteanalytics/dashboard.html", context)


@csrf_exempt
def track_click(request):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    target = str(payload.get("target", ""))[:500]
    source = str(payload.get("source", ""))[:500]
    label = str(payload.get("label", ""))[:220]
    if not target.startswith("/") or any(target.startswith(prefix) for prefix in PRIVATE_PREFIXES):
        return JsonResponse({"ok": True})
    try:
        ClickEvent.objects.create(
            visitor_hash=visitor_hash(request),
            source_path=source,
            target_path=target,
            label=label,
        )
    except Exception:
        pass
    return JsonResponse({"ok": True})
