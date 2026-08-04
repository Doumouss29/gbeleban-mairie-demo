from .models import SiteSettings, Page


def site_context(request):
    # L'administration Django n'a pas besoin du contexte du portail public.
    # On l'exclut explicitement afin d'isoler totalement /admin/ du CMS public.
    if request.path.startswith('/admin/'):
        return {}

    try:
        settings_obj = SiteSettings.objects.first()
        menu_pages = Page.objects.filter(is_published=True, show_in_menu=True)
        return {"site_settings": settings_obj, "menu_pages": menu_pages}
    except Exception:
        # Le site doit rester accessible même si la base de démo est en cours
        # d'initialisation pendant un redéploiement Render.
        return {"site_settings": None, "menu_pages": []}
