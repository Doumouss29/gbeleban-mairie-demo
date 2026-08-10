from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("portal", "0008_contact_form"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParcelOwner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("person_type", models.CharField(choices=[("physical", "Personne physique"), ("legal", "Personne morale")], default="physical", max_length=20, verbose_name="Type de propriétaire")),
                ("last_name", models.CharField(blank=True, max_length=160, verbose_name="Nom")),
                ("first_names", models.CharField(blank=True, max_length=220, verbose_name="Prénoms")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="Date de naissance")),
                ("birth_place", models.CharField(blank=True, max_length=180, verbose_name="Lieu de naissance")),
                ("nationality", models.CharField(blank=True, max_length=100, verbose_name="Nationalité")),
                ("profession", models.CharField(blank=True, max_length=160, verbose_name="Profession")),
                ("legal_name", models.CharField(blank=True, max_length=240, verbose_name="Raison sociale / dénomination")),
                ("legal_form", models.CharField(blank=True, max_length=100, verbose_name="Forme juridique")),
                ("registration_number", models.CharField(blank=True, max_length=120, verbose_name="N° RCCM / immatriculation")),
                ("tax_number", models.CharField(blank=True, max_length=120, verbose_name="Identifiant fiscal")),
                ("representative_name", models.CharField(blank=True, max_length=220, verbose_name="Représentant")),
                ("representative_function", models.CharField(blank=True, max_length=160, verbose_name="Fonction du représentant")),
                ("phone", models.CharField(blank=True, max_length=80, verbose_name="Téléphone")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="E-mail")),
                ("address", models.CharField(blank=True, max_length=320, verbose_name="Adresse")),
                ("identity_type", models.CharField(blank=True, max_length=80, verbose_name="Type de pièce")),
                ("identity_number", models.CharField(blank=True, max_length=120, verbose_name="N° de pièce")),
                ("identity_document_name", models.CharField(blank=True, max_length=255, verbose_name="Nom du fichier d'identité")),
                ("identity_document_type", models.CharField(blank=True, max_length=120, verbose_name="Type MIME")),
                ("identity_document_data", models.BinaryField(blank=True, editable=False, null=True, verbose_name="Pièce d'identité")),
                ("notes", models.TextField(blank=True, verbose_name="Observations")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="parcel_owners_created", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Propriétaire cadastral", "verbose_name_plural": "Propriétaires cadastraux", "ordering": ["legal_name", "last_name", "first_names", "id"]},
        ),
        migrations.CreateModel(
            name="ParcelOwnership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("owner", "Propriétaire"), ("coowner", "Copropriétaire"), ("landowner", "Propriétaire terrien"), ("acquirer", "Acquéreur")], default="owner", max_length=20, verbose_name="Qualité")),
                ("share_percentage", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Quote-part (%)")),
                ("start_date", models.DateField(blank=True, null=True, verbose_name="Début de propriété")),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="Fin de propriété")),
                ("is_current", models.BooleanField(db_index=True, default=True, verbose_name="Propriétaire actuel")),
                ("source", models.CharField(blank=True, max_length=160, verbose_name="Source")),
                ("source_reference", models.CharField(blank=True, max_length=180, verbose_name="Référence de l'acte / source")),
                ("notes", models.TextField(blank=True, verbose_name="Observations")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="parcel_ownerships_created", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="parcel_rights", to="portal.parcelowner", verbose_name="Propriétaire")),
                ("parcel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ownership_records", to="portal.parcel", verbose_name="Parcelle")),
            ],
            options={"verbose_name": "Historique de propriété", "verbose_name_plural": "Historiques de propriété", "ordering": ["-is_current", "-start_date", "-created_at"]},
        ),
        migrations.AddIndex(model_name="parcelowner", index=models.Index(fields=["person_type"], name="portal_owner_type_idx")),
        migrations.AddIndex(model_name="parcelowner", index=models.Index(fields=["last_name", "first_names"], name="portal_owner_name_idx")),
        migrations.AddIndex(model_name="parcelowner", index=models.Index(fields=["legal_name"], name="portal_owner_legal_idx")),
        migrations.AddIndex(model_name="parcelownership", index=models.Index(fields=["parcel", "is_current"], name="portal_parcel_current_idx")),
        migrations.AddIndex(model_name="parcelownership", index=models.Index(fields=["owner", "is_current"], name="portal_owner_current_idx")),
        migrations.AddIndex(model_name="parcelownership", index=models.Index(fields=["start_date", "end_date"], name="portal_owner_period_idx")),
    ]
