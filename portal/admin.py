from django.contrib import admin
from .models import SiteSettings, Page, QuickLink, News, Project, MapLayer, MapFeature, Parcel, Taxpayer, Tax, Payment

admin.site.site_header = "Administration - Commune de Gbéléban"
admin.site.site_title = "Gbéléban Admin"
admin.site.index_title = "Pilotage du portail municipal"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identité de la commune", {
            "fields": ("municipality_name", "municipality_logo_src", "national_arms_src")
        }),
        ("Bannière d'accueil", {
            "fields": ("hero_title", "hero_text", "hero_image_url")
        }),
        ("Le mot du maire", {
            "fields": ("mayor_name", "mayor_message", "mayor_image_url")
        }),
        ("Coordonnées", {
            "fields": ("phone", "email", "address")
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_menu", "menu_order")
    list_editable = ("is_published", "show_in_menu", "menu_order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(QuickLink)
class QuickLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "is_active", "order")
    list_editable = ("is_active", "order")


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_published")
    list_filter = ("is_published", "published_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "progress", "budget", "is_published")
    list_editable = ("status", "progress", "is_published")
    list_filter = ("status", "category")


@admin.register(MapLayer)
class MapLayerAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_public", "is_default_visible")
    list_editable = ("is_public", "is_default_visible")


admin.site.register(MapFeature)
admin.site.register(Parcel)
admin.site.register(Taxpayer)
admin.site.register(Tax)
admin.site.register(Payment)
