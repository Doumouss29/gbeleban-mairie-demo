from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0008_contact_form"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="home_projects_image_src",
            field=models.TextField(blank=True, verbose_name="Image accueil - Nos projets"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="home_map_image_src",
            field=models.TextField(blank=True, verbose_name="Image accueil - Gbéléban en carte"),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="home_address_image_src",
            field=models.TextField(blank=True, verbose_name="Image accueil - Adressage Gbéléban"),
        ),
    ]
