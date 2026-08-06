from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("portal", "0004_news_project_gallery"),
    ]

    operations = [
        migrations.CreateModel(
            name="MunicipalRevenueTheme",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True, verbose_name="Thématique de recette")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("frequency", models.CharField(choices=[("daily", "Quotidienne"), ("weekly", "Hebdomadaire"), ("monthly", "Mensuelle")], default="daily", max_length=20, verbose_name="Périodicité")),
                ("target_amount", models.DecimalField(blank=True, decimal_places=0, max_digits=16, null=True, verbose_name="Objectif par période (FCFA)")),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="municipal_revenue_themes", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Thématique de collecte municipale",
                "verbose_name_plural": "Thématiques de collecte municipale",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="MunicipalRevenueEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("collection_date", models.DateField(verbose_name="Date de collecte")),
                ("amount", models.DecimalField(decimal_places=0, max_digits=16, verbose_name="Montant collecté (FCFA)")),
                ("comment", models.TextField(blank=True, verbose_name="Commentaire")),
                ("receipt_reference", models.CharField(blank=True, max_length=120, verbose_name="Référence / quittance")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="municipal_revenue_entries", to=settings.AUTH_USER_MODEL)),
                ("theme", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entries", to="portal.municipalrevenuetheme")),
            ],
            options={
                "verbose_name": "Collecte municipale",
                "verbose_name_plural": "Collectes municipales",
                "ordering": ["-collection_date", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="municipalrevenueentry",
            index=models.Index(fields=["collection_date"], name="portal_muni_collect_2837f4_idx"),
        ),
        migrations.AddIndex(
            model_name="municipalrevenueentry",
            index=models.Index(fields=["theme", "collection_date"], name="portal_muni_theme_i_2992e1_idx"),
        ),
    ]
