from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MapLayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Nom")),
                ("category", models.CharField(blank=True, max_length=100, verbose_name="Catégorie")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("color", models.CharField(default="#f28c28", max_length=20, verbose_name="Couleur")),
                ("is_public", models.BooleanField(default=True, verbose_name="Visible sur la carte publique")),
                ("is_default_visible", models.BooleanField(default=True, verbose_name="Visible au démarrage")),
                ("display_fields", models.JSONField(blank=True, default=list, verbose_name="Champs à afficher")),
            ],
        ),
        migrations.CreateModel(
            name="News",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Titre")),
                ("excerpt", models.TextField(blank=True, verbose_name="Résumé")),
                ("body", models.TextField(blank=True, verbose_name="Contenu")),
                ("image_url", models.URLField(blank=True, verbose_name="Image (URL)")),
                ("published_at", models.DateField(verbose_name="Date de publication")),
                ("is_published", models.BooleanField(default=True, verbose_name="Publiée")),
            ],
            options={"ordering": ["-published_at"]},
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="Titre")),
                ("slug", models.SlugField(unique=True, verbose_name="Adresse URL")),
                ("summary", models.CharField(blank=True, max_length=300, verbose_name="Résumé")),
                ("content", models.TextField(verbose_name="Contenu")),
                ("image_url", models.URLField(blank=True, verbose_name="Image (URL)")),
                ("is_published", models.BooleanField(default=True, verbose_name="Publiée")),
                ("show_in_menu", models.BooleanField(default=True, verbose_name="Afficher dans le menu")),
                ("menu_order", models.PositiveIntegerField(default=100, verbose_name="Ordre")),
            ],
            options={"ordering": ["menu_order", "title"]},
        ),
        migrations.CreateModel(
            name="Parcel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(max_length=120, unique=True, verbose_name="Référence")),
                ("section", models.CharField(blank=True, max_length=80, verbose_name="Section")),
                ("ilot", models.CharField(blank=True, max_length=80, verbose_name="Îlot")),
                ("lot", models.CharField(blank=True, max_length=80, verbose_name="Lot")),
                ("parcel_number", models.CharField(blank=True, max_length=80, verbose_name="N° parcelle")),
                ("area_m2", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name="Superficie m²")),
                ("usage", models.CharField(blank=True, max_length=120, verbose_name="Usage")),
                ("geometry", models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Titre")),
                ("category", models.CharField(blank=True, max_length=100, verbose_name="Catégorie")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                ("status", models.CharField(choices=[("done", "Réalisé"), ("ongoing", "En cours"), ("planned", "À venir")], default="planned", max_length=20, verbose_name="Statut")),
                ("progress", models.PositiveSmallIntegerField(default=0, verbose_name="Avancement (%)")),
                ("budget", models.DecimalField(blank=True, decimal_places=0, max_digits=18, null=True, verbose_name="Budget FCFA")),
                ("image_url", models.URLField(blank=True, verbose_name="Image (URL)")),
                ("latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("is_published", models.BooleanField(default=True, verbose_name="Publié")),
            ],
        ),
        migrations.CreateModel(
            name="QuickLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120, verbose_name="Titre")),
                ("description", models.CharField(blank=True, max_length=220, verbose_name="Description")),
                ("icon", models.CharField(default="→", max_length=20, verbose_name="Icône")),
                ("url", models.CharField(default="#", max_length=255, verbose_name="Lien")),
                ("is_active", models.BooleanField(default=True, verbose_name="Actif")),
                ("order", models.PositiveIntegerField(default=100, verbose_name="Ordre")),
            ],
            options={"ordering": ["order", "title"]},
        ),
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("municipality_name", models.CharField(default="Commune de Gbéléban", max_length=120, verbose_name="Nom de la commune")),
                ("hero_title", models.CharField(default="Bienvenue à Gbéléban", max_length=180, verbose_name="Titre principal")),
                ("hero_text", models.TextField(default="Une commune proche de ses habitants, tournée vers le développement.", verbose_name="Texte principal")),
                ("mayor_name", models.CharField(default="Madame le Maire", max_length=160, verbose_name="Nom du maire")),
                ("mayor_message", models.TextField(default="Bienvenue sur le portail numérique de la Commune de Gbéléban.", verbose_name="Mot du maire")),
                ("phone", models.CharField(blank=True, max_length=60, verbose_name="Téléphone")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="E-mail")),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="Adresse")),
                ("municipality_logo_src", models.TextField(blank=True, verbose_name="Logo / armoirie de la commune")),
                ("national_arms_src", models.TextField(blank=True, verbose_name="Armoiries de Côte d'Ivoire")),
                ("hero_image_url", models.TextField(blank=True, verbose_name="Image de couverture (URL ou image importée)")),
                ("mayor_hero_image_url", models.TextField(blank=True, verbose_name="Photo du maire - bloc d'accueil")),
                ("mayor_section_image_url", models.TextField(blank=True, verbose_name="Photo du maire - section Le mot du Maire")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Configuration du site", "verbose_name_plural": "Configuration du site"},
        ),
        migrations.CreateModel(
            name="MapFeature",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("properties", models.JSONField(default=dict)),
                ("geometry", models.JSONField(default=dict)),
                ("layer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="features", to="portal.maplayer")),
            ],
        ),
        migrations.CreateModel(
            name="Taxpayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180, verbose_name="Nom / raison sociale")),
                ("phone", models.CharField(blank=True, max_length=60, verbose_name="Téléphone")),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="Adresse")),
                ("parcel", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="taxpayers", to="portal.parcel")),
            ],
        ),
        migrations.CreateModel(
            name="Tax",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(max_length=160, verbose_name="Type de taxe")),
                ("year", models.PositiveIntegerField(verbose_name="Année")),
                ("amount_due", models.DecimalField(decimal_places=0, max_digits=14, verbose_name="Montant dû")),
                ("status", models.CharField(choices=[("unpaid", "Impayée"), ("partial", "Partielle"), ("paid", "Payée")], default="unpaid", max_length=20, verbose_name="Statut")),
                ("taxpayer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="taxes", to="portal.taxpayer")),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=0, max_digits=14, verbose_name="Montant")),
                ("paid_at", models.DateField(verbose_name="Date de paiement")),
                ("method", models.CharField(blank=True, max_length=80, verbose_name="Mode de paiement")),
                ("reference", models.CharField(blank=True, max_length=120, verbose_name="Référence")),
                ("tax", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="portal.tax")),
            ],
        ),
    ]
