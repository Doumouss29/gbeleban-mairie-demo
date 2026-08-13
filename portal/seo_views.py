from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import escape
from .models import News, Page

BASE_URL = "https://mairie-gbeleban.ci"


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /connexion/",
        "Disallow: /mon-espace/",
        "Disallow: /urbanisme/",
        "Disallow: /dashboard/",
        "Disallow: /collecte-municipale/",
        "Disallow: /pilotage-projets/",
        "Disallow: /gestion/",
        f"Sitemap: {BASE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    urls = [
        ("/", "1.0", "weekly"),
        ("/pages/la-commune/", "0.9", "monthly"),
        ("/gbeleban-en-carte/", "0.9", "monthly"),
        ("/projets/", "0.9", "weekly"),
        ("/actualites/", "0.9", "daily"),
        ("/pages/contact/", "0.7", "monthly"),
    ]

    for page in Page.objects.filter(is_published=True).exclude(slug__in=["la-commune", "contact"]):
        urls.append((page.get_absolute_url(), "0.7", "monthly"))

    for item in News.objects.filter(is_published=True).only("id"):
        urls.append((reverse("news_detail", kwargs={"news_id": item.id}), "0.8", "weekly"))

    entries = []
    for path, priority, changefreq in urls:
        entries.append(
            "<url>"
            f"<loc>{escape(BASE_URL + path)}</loc>"
            f"<changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority>"
            "</url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(entries)
        + "</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
