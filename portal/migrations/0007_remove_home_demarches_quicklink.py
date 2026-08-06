from django.db import migrations


def remove_demarches_quicklink(apps, schema_editor):
    QuickLink = apps.get_model("portal", "QuickLink")
    QuickLink.objects.filter(title="Mes démarches").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0006_remove_default_welcome_news"),
    ]

    operations = [
        migrations.RunPython(remove_demarches_quicklink, migrations.RunPython.noop),
    ]
