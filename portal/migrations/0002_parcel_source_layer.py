from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="parcel",
            name="source_layer",
            field=models.CharField(blank=True, db_index=True, max_length=160, verbose_name="Couche d'origine"),
        ),
        migrations.AlterField(
            model_name="parcel",
            name="reference",
            field=models.CharField(max_length=120, verbose_name="Référence"),
        ),
        migrations.AddConstraint(
            model_name="parcel",
            constraint=models.UniqueConstraint(fields=("source_layer", "reference"), name="uniq_parcel_layer_reference"),
        ),
    ]
