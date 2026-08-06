from django.db import migrations, models


def seed_default_recipient(apps, schema_editor):
    ContactRecipient = apps.get_model("portal", "ContactRecipient")
    ContactRecipient.objects.get_or_create(
        email="doumbiasmoussa@gmail.com",
        defaults={"label": "Contact principal", "is_active": True},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0007_remove_home_demarches_quicklink"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactRecipient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="Adresse e-mail")),
                ("label", models.CharField(blank=True, help_text="Ex. Secrétariat, Maire, Service communication", max_length=120, verbose_name="Libellé")),
                ("is_active", models.BooleanField(default=True, verbose_name="Recevoir les messages")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Destinataire des contacts",
                "verbose_name_plural": "Destinataires des contacts",
                "ordering": ["email"],
            },
        ),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="Nom")),
                ("email", models.EmailField(max_length=254, verbose_name="E-mail")),
                ("phone", models.CharField(blank=True, max_length=60, verbose_name="Téléphone")),
                ("subject", models.CharField(max_length=200, verbose_name="Objet")),
                ("message", models.TextField(verbose_name="Message")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Reçu le")),
                ("email_sent", models.BooleanField(default=False, verbose_name="E-mail envoyé")),
                ("is_processed", models.BooleanField(default=False, verbose_name="Traité")),
            ],
            options={
                "verbose_name": "Message de contact",
                "verbose_name_plural": "Messages de contact",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(seed_default_recipient, migrations.RunPython.noop),
    ]
