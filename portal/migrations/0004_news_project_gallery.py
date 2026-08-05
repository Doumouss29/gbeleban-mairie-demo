from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0003_urbanismlayer_parcel_properties"),
    ]

    operations = [
        migrations.AddField(model_name="news", name="image_1_src", field=models.TextField(blank=True, verbose_name="Image 1")),
        migrations.AddField(model_name="news", name="image_2_src", field=models.TextField(blank=True, verbose_name="Image 2")),
        migrations.AddField(model_name="news", name="image_3_src", field=models.TextField(blank=True, verbose_name="Image 3")),
        migrations.AlterField(model_name="news", name="image_url", field=models.URLField(blank=True, verbose_name="Image historique (URL)")),
        migrations.AddField(model_name="project", name="image_1_src", field=models.TextField(blank=True, verbose_name="Image 1")),
        migrations.AddField(model_name="project", name="image_2_src", field=models.TextField(blank=True, verbose_name="Image 2")),
        migrations.AddField(model_name="project", name="image_3_src", field=models.TextField(blank=True, verbose_name="Image 3")),
        migrations.AlterField(model_name="project", name="image_url", field=models.URLField(blank=True, verbose_name="Image historique (URL)")),
    ]
