from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0002_parcel_source_layer"),
    ]

    operations = [
        migrations.CreateModel(
            name="UrbanismLayer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True, verbose_name="Nom de la couche")),
                ("display_fields", models.JSONField(blank=True, default=list, verbose_name="Champs à afficher")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="parcel",
            name="properties",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
