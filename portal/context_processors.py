from .models import SiteSettings, Page

def site_context(request):
    settings_obj = SiteSettings.objects.first()
    menu_pages = Page.objects.filter(is_published=True, show_in_menu=True)
    return {"site_settings": settings_obj, "menu_pages": menu_pages}
