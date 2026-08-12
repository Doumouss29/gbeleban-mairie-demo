from django.conf import settings
from django.db import models


class ProjectPilotage(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planifié"),
        ("ongoing", "En cours"),
        ("paused", "En pause"),
        ("done", "Terminé"),
    ]

    title = models.CharField("Nom du projet", max_length=200)
    description = models.TextField("Description", blank=True)
    image_src = models.TextField("Image", blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="planned")
    progress = models.PositiveSmallIntegerField("Avancement (%)", default=0)
    budget_planned = models.DecimalField("Budget prévisionnel (FCFA)", max_digits=18, decimal_places=0, null=True, blank=True)
    budget_spent = models.DecimalField("Dépenses engagées (FCFA)", max_digits=18, decimal_places=0, default=0)
    start_date = models.DateField("Date de début", null=True, blank=True)
    end_date = models.DateField("Date de fin prévue", null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="pilotage_projects", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="pilotage_projects_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "title"]
        verbose_name = "Projet piloté"
        verbose_name_plural = "Projets pilotés"

    def __str__(self):
        return self.title

    @property
    def budget_remaining(self):
        if self.budget_planned is None:
            return None
        return self.budget_planned - (self.budget_spent or 0)


class ProjectStep(models.Model):
    STATUS_CHOICES = [
        ("todo", "À faire"),
        ("ongoing", "En cours"),
        ("blocked", "Bloqué"),
        ("done", "Terminé"),
    ]

    project = models.ForeignKey(ProjectPilotage, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField("Étape", max_length=200)
    description = models.TextField("Description", blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="todo")
    progress = models.PositiveSmallIntegerField("Avancement (%)", default=0)
    start_date = models.DateField("Début", null=True, blank=True)
    end_date = models.DateField("Fin prévue", null=True, blank=True)
    budget = models.DecimalField("Budget étape (FCFA)", max_digits=18, decimal_places=0, null=True, blank=True)
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="pilotage_steps")
    order = models.PositiveIntegerField("Ordre", default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "start_date", "id"]
        verbose_name = "Étape de projet"
        verbose_name_plural = "Étapes de projet"

    def __str__(self):
        return f"{self.project} — {self.title}"
