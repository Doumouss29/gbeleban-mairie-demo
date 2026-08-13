from .models import SiteSettings, Page, News


def _seo_description(request, settings_obj):
    path = request.path
    mayor = ""
    if settings_obj and settings_obj.mayor_name:
        mayor = f" Sous la conduite de {settings_obj.mayor_name}, Maire de Gbéléban."

    descriptions = {
        "/": "Site officiel de la Mairie de Gbéléban, commune du Kabadougou dans le District du Denguélé en Côte d’Ivoire. Actualités, projets, services municipaux et cartographie de Gbéléban.",
        "/pages/la-commune/": "Découvrez Gbéléban, commune de la région du Kabadougou dans le District du Denguélé en Côte d’Ivoire : territoire, population, vie locale, culture et développement municipal.",
        "/gbeleban-en-carte/": "Explorez la carte interactive de Gbéléban dans le Kabadougou : équipements publics, éducation, santé, commerces, transports, loisirs, environnement et services de la commune.",
        "/projets/": "Découvrez les projets et réalisations de la Mairie de Gbéléban : aménagement, équipements, infrastructures et actions de développement dans la commune du Kabadougou.",
        "/actualites/": "Retrouvez les actualités de la Mairie de Gbéléban, les actions du Conseil municipal, les projets et les informations de la commune dans la région du Kabadougou.",
        "/pages/contact/": "Contactez la Mairie de Gbéléban pour vos demandes et informations municipales. Commune de Gbéléban, région du Kabadougou, District du Denguélé, Côte d’Ivoire.",
    }

    if path in descriptions:
        return descriptions[path] + mayor

    if path.startswith("/actualites/"):
        try:
            news_id = int(path.strip("/").split("/")[-1])
            item = News.objects.filter(pk=news_id, is_published=True).first()
            if item:
                text = (item.excerpt or item.body or "").replace("\n", " ").strip()
                if len(text) > 150:
                    text = text[:147].rstrip() + "…"
                return f"{item.title} — Actualité officielle de la Mairie de Gbéléban, commune du Kabadougou. {text}".strip()
        except (ValueError, TypeError):
            pass

    if path.startswith("/pages/"):
        slug = path.strip("/").split("/")[-1]
        page = Page.objects.filter(slug=slug, is_published=True).first()
        if page:
            text = (page.summary or page.content or "").replace("\n", " ").strip()
            if len(text) > 155:
                text = text[:152].rstrip() + "…"
            return f"{page.title} — Mairie de Gbéléban, commune du Kabadougou. {text}".strip()

    return "Portail officiel de la Mairie de Gbéléban, commune de la région du Kabadougou dans le District du Denguélé en Côte d’Ivoire." + mayor


def site_context(request):
    # L'administration Django n'a pas besoin du contexte du portail public.
    if request.path.startswith('/admin/'):
        return {}

    try:
        settings_obj = SiteSettings.objects.first()
        menu_pages = Page.objects.filter(is_published=True, show_in_menu=True)
        return {
            "site_settings": settings_obj,
            "menu_pages": menu_pages,
            "seo_description": _seo_description(request, settings_obj),
        }
    except Exception:
        return {
            "site_settings": None,
            "menu_pages": [],
            "seo_description": "Portail officiel de la Mairie de Gbéléban, commune de la région du Kabadougou dans le District du Denguélé en Côte d’Ivoire.",
        }
