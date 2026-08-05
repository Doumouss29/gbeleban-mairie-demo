from django.contrib import admin
from .forms import SiteSettingsAdminForm, NewsAdminForm, ProjectAdminForm
from .models import SiteSettings, Page, QuickLink, News, Project, MapLayer, MapFeature, Parcel, Taxpayer, Tax, Payment

admin.site.site_header = "Administration - Commune de Gbéléban"
admin.site.site_title = "Gbéléban Admin"
admin.site.index_title = "Pilotage du portail municipal"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsAdminForm
    fieldsets = (
        ("Identité de la commune", {"fields": ("municipality_name", "municipality_logo_upload", "municipality_logo_src", "national_arms_upload", "national_arms_src")}),
        ("Bannière d'accueil", {"fields": ("hero_title", "hero_text", "hero_image_upload", "hero_image_url")}),
        ("Le mot du maire", {"fields": ("mayor_name", "mayor_message", "mayor_hero_image_upload", "mayor_hero_image_url", "mayor_section_image_upload", "mayor_section_image_url")}),
        ("Coordonnées", {"fields": ("phone", "email", "address")}),
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
    form = NewsAdminForm
    list_display = ("title", "published_at", "is_published")
    list_filter = ("is_published", "published_at")
    fieldsets = (
        ("Actualité", {"fields": ("title", "excerpt", "body", "published_at", "is_published")}),
        ("Galerie - 1 à 3 images", {"fields": (
            "image_1_upload", "image_1_src",
            "image_2_upload", "image_2_src",
            "image_3_upload", "image_3_src",
            "image_url",
        )}),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ("title", "category", "status", "progress", "budget", "is_published")
    list_editable = ("status", "progress", "is_published")
    list_filter = ("status", "category")
    fieldsets = (
        ("Projet", {"fields": ("title", "category", "description", "status", "progress", "budget", "latitude", "longitude", "is_published")}),
        ("Galerie - 1 à 3 images", {"fields": (
            "image_1_upload", "image_1_src",
            "image_2_upload", "image_2_src",
            "image_3_upload", "image_3_src",
            "image_url",
        )}),
    )


@admin.register(MapLayer)
class MapLayerAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_public", "is_default_visible")
    list_editable = ("is_public", "is_default_visible")


admin.site.register(MapFeature)
admin.site.register(Parcel)
admin.site.register(Taxpayer)
admin.site.register(Tax)
admin.site.register(Payment)
