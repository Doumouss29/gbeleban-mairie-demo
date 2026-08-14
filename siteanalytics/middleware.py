import hashlib
import ipaddress
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings

from .models import PageVisit, VisitorGeo


BOT_MARKERS = (
    "bot", "spider", "crawl", "slurp", "bingpreview", "facebookexternalhit",
    "whatsapp", "telegrambot", "python-requests", "curl/", "wget/",
)

EXCLUDED_PREFIXES = (
    "/static/", "/admin/", "/gestion/", "/connexion/", "/deconnexion/",
    "/mon-espace/", "/urbanisme/", "/dashboard/", "/collecte-municipale/",
    "/pilotage-projets/", "/api/", "/analytics/",
)

EXCLUDED_PATHS = ("/robots.txt", "/sitemap.xml", "/favicon.ico")


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "")


def visitor_hash(request):
    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
    raw = f"{settings.SECRET_KEY}|{ip}|{user_agent}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()


def _is_public_ip(value):
    try:
        ip = ipaddress.ip_address(value)
        return not (ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_multicast)
    except ValueError:
        return False


def _lookup_geo(ip):
    if not _is_public_ip(ip):
        return {}
    try:
        req = Request(
            f"https://ipwho.is/{quote(ip)}",
            headers={"User-Agent": "Mairie-Gbeleban-Analytics/1.0"},
        )
        with urlopen(req, timeout=1.2) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data.get("success", False):
            return {}
        return {
            "country": (data.get("country") or "")[:120],
            "country_code": (data.get("country_code") or "")[:8],
            "region": (data.get("region") or "")[:160],
            "city": (data.get("city") or "")[:160],
        }
    except Exception:
        return {}


def get_geo_for_visitor(request, vhash):
    cached = VisitorGeo.objects.filter(visitor_hash=vhash).first()
    if cached:
        return {
            "country": cached.country,
            "country_code": cached.country_code,
            "region": cached.region,
            "city": cached.city,
        }
    geo = _lookup_geo(get_client_ip(request))
    VisitorGeo.objects.create(visitor_hash=vhash, **geo)
    return geo


def detect_device(user_agent):
    ua = (user_agent or "").lower()
    if any(x in ua for x in ("ipad", "tablet", "kindle")):
        return "Tablette"
    if any(x in ua for x in ("iphone", "android", "mobile", "opera mini", "windows phone")):
        return "Mobile"
    return "Ordinateur"


def should_track(request, response):
    if request.method != "GET" or response.status_code >= 400:
        return False
    path = request.path
    if path in EXCLUDED_PATHS or any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    content_type = response.get("Content-Type", "")
    if "text/html" not in content_type:
        return False
    ua = request.META.get("HTTP_USER_AGENT", "").lower()
    return not any(marker in ua for marker in BOT_MARKERS)


class SiteAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if should_track(request, response):
            try:
                vhash = visitor_hash(request)
                geo = get_geo_for_visitor(request, vhash)
                PageVisit.objects.create(
                    visitor_hash=vhash,
                    path=request.path[:500],
                    referer=request.META.get("HTTP_REFERER", "")[:500],
                    device=detect_device(request.META.get("HTTP_USER_AGENT", "")),
                    country=geo.get("country", ""),
                    region=geo.get("region", ""),
                    city=geo.get("city", ""),
                )
            except Exception:
                # Les statistiques ne doivent jamais empêcher le site de répondre.
                pass
        return response
