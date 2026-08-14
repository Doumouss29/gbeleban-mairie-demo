from django.db import models


class VisitorGeo(models.Model):
    visitor_hash = models.CharField(max_length=64, unique=True, db_index=True)
    country = models.CharField(max_length=120, blank=True)
    country_code = models.CharField(max_length=8, blank=True)
    region = models.CharField(max_length=160, blank=True)
    city = models.CharField(max_length=160, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Localisation visiteur"
        verbose_name_plural = "Localisations visiteurs"

    def __str__(self):
        return " / ".join(x for x in (self.country, self.region, self.city) if x) or "Localisation inconnue"


class PageVisit(models.Model):
    visitor_hash = models.CharField(max_length=64, db_index=True)
    path = models.CharField(max_length=500, db_index=True)
    referer = models.CharField(max_length=500, blank=True)
    device = models.CharField(max_length=30, blank=True, db_index=True)
    country = models.CharField(max_length=120, blank=True, db_index=True)
    region = models.CharField(max_length=160, blank=True, db_index=True)
    city = models.CharField(max_length=160, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Visite de page"
        verbose_name_plural = "Visites de pages"
        indexes = [
            models.Index(fields=["created_at", "path"], name="analytics_visit_date_path"),
            models.Index(fields=["created_at", "visitor_hash"], name="analytics_visit_date_user"),
        ]

    def __str__(self):
        return f"{self.path} - {self.created_at:%d/%m/%Y %H:%M}"


class ClickEvent(models.Model):
    visitor_hash = models.CharField(max_length=64, db_index=True)
    source_path = models.CharField(max_length=500, blank=True)
    target_path = models.CharField(max_length=500, db_index=True)
    label = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Clic"
        verbose_name_plural = "Clics"
        indexes = [models.Index(fields=["created_at", "target_path"], name="analytics_click_date_target")]

    def __str__(self):
        return f"{self.source_path} → {self.target_path}"
