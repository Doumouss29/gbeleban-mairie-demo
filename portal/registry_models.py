from django.conf import settings
from django.db import models


class ParcelOwner(models.Model):
    PERSON_TYPE_PHYSICAL = "physical"
    PERSON_TYPE_LEGAL = "legal"
    PERSON_TYPE_CHOICES = [
        (PERSON_TYPE_PHYSICAL, "Personne physique"),
        (PERSON_TYPE_LEGAL, "Personne morale"),
    ]

    person_type = models.CharField("Type de propriétaire", max_length=20, choices=PERSON_TYPE_CHOICES, default=PERSON_TYPE_PHYSICAL)
    last_name = models.CharField("Nom", max_length=160, blank=True)
    first_names = models.CharField("Prénoms", max_length=220, blank=True)
    birth_date = models.DateField("Date de naissance", null=True, blank=True)
    birth_place = models.CharField("Lieu de naissance", max_length=180, blank=True)
    nationality = models.CharField("Nationalité", max_length=100, blank=True)
    profession = models.CharField("Profession", max_length=160, blank=True)

    legal_name = models.CharField("Raison sociale / dénomination", max_length=240, blank=True)
    legal_form = models.CharField("Forme juridique", max_length=100, blank=True)
    registration_number = models.CharField("N° RCCM / immatriculation", max_length=120, blank=True)
    tax_number = models.CharField("Identifiant fiscal", max_length=120, blank=True)
    representative_name = models.CharField("Représentant", max_length=220, blank=True)
    representative_function = models.CharField("Fonction du représentant", max_length=160, blank=True)

    phone = models.CharField("Téléphone", max_length=80, blank=True)
    email = models.EmailField("E-mail", blank=True)
    address = models.CharField("Adresse", max_length=320, blank=True)

    identity_type = models.CharField("Type de pièce", max_length=80, blank=True)
    identity_number = models.CharField("N° de pièce", max_length=120, blank=True)
    identity_document_name = models.CharField("Nom du fichier d'identité", max_length=255, blank=True)
    identity_document_type = models.CharField("Type MIME", max_length=120, blank=True)
    identity_document_data = models.BinaryField("Pièce d'identité", null=True, blank=True, editable=False)

    notes = models.TextField("Observations", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="parcel_owners_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "portal"
        ordering = ["legal_name", "last_name", "first_names", "id"]
        verbose_name = "Propriétaire cadastral"
        verbose_name_plural = "Propriétaires cadastraux"
        indexes = [
            models.Index(fields=["person_type"], name="portal_owner_type_idx"),
            models.Index(fields=["last_name", "first_names"], name="portal_owner_name_idx"),
            models.Index(fields=["legal_name"], name="portal_owner_legal_idx"),
        ]

    @property
    def display_name(self):
        if self.person_type == self.PERSON_TYPE_LEGAL:
            return self.legal_name or self.representative_name or f"Personne morale #{self.pk}"
        name = " ".join(x for x in [self.last_name, self.first_names] if x).strip()
        return name or f"Propriétaire #{self.pk}"

    def __str__(self):
        return self.display_name


class ParcelOwnership(models.Model):
    ROLE_OWNER = "owner"
    ROLE_COOWNER = "coowner"
    ROLE_LANDOWNER = "landowner"
    ROLE_ACQUIRER = "acquirer"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Propriétaire"),
        (ROLE_COOWNER, "Copropriétaire"),
        (ROLE_LANDOWNER, "Propriétaire terrien"),
        (ROLE_ACQUIRER, "Acquéreur"),
    ]

    parcel = models.ForeignKey("portal.Parcel", on_delete=models.CASCADE, related_name="ownership_records", verbose_name="Parcelle")
    owner = models.ForeignKey(ParcelOwner, on_delete=models.PROTECT, related_name="parcel_rights", verbose_name="Propriétaire")
    role = models.CharField("Qualité", max_length=20, choices=ROLE_CHOICES, default=ROLE_OWNER)
    share_percentage = models.DecimalField("Quote-part (%)", max_digits=6, decimal_places=2, null=True, blank=True)
    start_date = models.DateField("Début de propriété", null=True, blank=True)
    end_date = models.DateField("Fin de propriété", null=True, blank=True)
    is_current = models.BooleanField("Propriétaire actuel", default=True, db_index=True)
    source = models.CharField("Source", max_length=160, blank=True)
    source_reference = models.CharField("Référence de l'acte / source", max_length=180, blank=True)
    notes = models.TextField("Observations", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="parcel_ownerships_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "portal"
        ordering = ["-is_current", "-start_date", "-created_at"]
        verbose_name = "Historique de propriété"
        verbose_name_plural = "Historiques de propriété"
        indexes = [
            models.Index(fields=["parcel", "is_current"], name="portal_parcel_current_idx"),
            models.Index(fields=["owner", "is_current"], name="portal_owner_current_idx"),
            models.Index(fields=["start_date", "end_date"], name="portal_owner_period_idx"),
        ]

    def __str__(self):
        return f"{self.parcel} — {self.owner.display_name}"
