from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="VisitorGeo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_hash", models.CharField(db_index=True, max_length=64, unique=True)),
                ("country", models.CharField(blank=True, max_length=120)),
                ("country_code", models.CharField(blank=True, max_length=8)),
                ("region", models.CharField(blank=True, max_length=160)),
                ("city", models.CharField(blank=True, max_length=160)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Localisation visiteur", "verbose_name_plural": "Localisations visiteurs"},
        ),
        migrations.CreateModel(
            name="PageVisit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_hash", models.CharField(db_index=True, max_length=64)),
                ("path", models.CharField(db_index=True, max_length=500)),
                ("referer", models.CharField(blank=True, max_length=500)),
                ("device", models.CharField(blank=True, db_index=True, max_length=30)),
                ("country", models.CharField(blank=True, db_index=True, max_length=120)),
                ("region", models.CharField(blank=True, db_index=True, max_length=160)),
                ("city", models.CharField(blank=True, db_index=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"verbose_name": "Visite de page", "verbose_name_plural": "Visites de pages", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ClickEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("visitor_hash", models.CharField(db_index=True, max_length=64)),
                ("source_path", models.CharField(blank=True, max_length=500)),
                ("target_path", models.CharField(db_index=True, max_length=500)),
                ("label", models.CharField(blank=True, max_length=220)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"verbose_name": "Clic", "verbose_name_plural": "Clics", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="pagevisit",
            index=models.Index(fields=["created_at", "path"], name="analytics_visit_date_path"),
        ),
        migrations.AddIndex(
            model_name="pagevisit",
            index=models.Index(fields=["created_at", "visitor_hash"], name="analytics_visit_date_user"),
        ),
        migrations.AddIndex(
            model_name="clickevent",
            index=models.Index(fields=["created_at", "target_path"], name="analytics_click_date_target"),
        ),
    ]
