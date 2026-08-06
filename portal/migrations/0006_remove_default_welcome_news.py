from django.db import migrations


def remove_default_welcome_news(apps, schema_editor):
    News = apps.get_model("portal", "News")
    News.objects.filter(title="Bienvenue sur le portail numérique de Gbéléban").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0005_municipal_revenue"),
    ]

    operations = [
        migrations.RunPython(remove_default_welcome_news, migrations.RunPython.noop),
    ]
