from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectPilotage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Nom du projet")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("image_src", models.TextField(blank=True, verbose_name="Image")),
                ("status", models.CharField(choices=[("planned", "Planifié"), ("ongoing", "En cours"), ("paused", "En pause"), ("done", "Terminé")], default="planned", max_length=20, verbose_name="Statut")),
                ("progress", models.PositiveSmallIntegerField(default=0, verbose_name="Avancement (%)")),
                ("budget_planned", models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True, verbose_name="Budget prévisionnel (FCFA)")),
                ("budget_spent", models.DecimalField(decimal_places=0, default=0, max_digits=18, verbose_name="Dépenses engagées (FCFA)")),
                ("start_date", models.DateField(blank=True, null=True, verbose_name="Date de début")),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="Date de fin prévue")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pilotage_projects_created", to=settings.AUTH_USER_MODEL)),
                ("members", models.ManyToManyField(blank=True, related_name="pilotage_projects", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Projet piloté", "verbose_name_plural": "Projets pilotés", "ordering": ["-updated_at", "title"]},
        ),
        migrations.CreateModel(
            name="ProjectStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Étape")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("status", models.CharField(choices=[("todo", "À faire"), ("ongoing", "En cours"), ("blocked", "Bloqué"), ("done", "Terminé")], default="todo", max_length=20, verbose_name="Statut")),
                ("progress", models.PositiveSmallIntegerField(default=0, verbose_name="Avancement (%)")),
                ("start_date", models.DateField(blank=True, null=True, verbose_name="Début")),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="Fin prévue")),
                ("budget", models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True, verbose_name="Budget étape (FCFA)")),
                ("order", models.PositiveIntegerField(default=100, verbose_name="Ordre")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="pilotage.projectpilotage")),
                ("responsible", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pilotage_steps", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Étape de projet", "verbose_name_plural": "Étapes de projet", "ordering": ["order", "start_date", "id"]},
        ),
    ]
