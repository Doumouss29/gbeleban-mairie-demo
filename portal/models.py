from django.conf import settings
from django.db import models
from django.urls import reverse


class SiteSettings(models.Model):
    municipality_name = models.CharField("Nom de la commune", max_length=120, default="Commune de Gbéléban")
    hero_title = models.CharField("Titre principal", max_length=180, default="Bienvenue à Gbéléban")
    hero_text = models.TextField("Texte principal", default="Une commune proche de ses habitants, tournée vers le développement.")
    mayor_name = models.CharField("Nom du maire", max_length=160, default="Madame le Maire")
    mayor_message = models.TextField("Mot du maire", default="Bienvenue sur le portail numérique de la Commune de Gbéléban.")
    phone = models.CharField("Téléphone", max_length=60, blank=True)
    email = models.EmailField("E-mail", blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    municipality_logo_src = models.TextField("Logo / armoirie de la commune", blank=True)
    national_arms_src = models.TextField("Armoiries de Côte d'Ivoire", blank=True)
    hero_image_url = models.TextField("Image de couverture (URL ou image importée)", blank=True)
    mayor_hero_image_url = models.TextField("Photo du maire - bloc d'accueil", blank=True)
    mayor_section_image_url = models.TextField("Photo du maire - section Le mot du Maire", blank=True)
    home_projects_image_src = models.TextField("Image accueil - Nos projets", blank=True)
    home_map_image_src = models.TextField("Image accueil - Gbéléban en carte", blank=True)
    home_address_image_src = models.TextField("Image accueil - Adressage Gbéléban", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration du site"
        verbose_name_plural = "Configuration du site"

    def __str__(self):
        return self.municipality_name


class Page(models.Model):
    title = models.CharField("Titre", max_length=180)
    slug = models.SlugField("Adresse URL", unique=True)
    summary = models.CharField("Résumé", max_length=300, blank=True)
    content = models.TextField("Contenu")
    image_url = models.URLField("Image (URL)", blank=True)
    is_published = models.BooleanField("Publiée", default=True)
    show_in_menu = models.BooleanField("Afficher dans le menu", default=True)
    menu_order = models.PositiveIntegerField("Ordre", default=100)

    class Meta:
        ordering = ["menu_order", "title"]

    def __str__(self): return self.title
    def get_absolute_url(self): return reverse("page_detail", kwargs={"slug": self.slug})


class ContactRecipient(models.Model):
    email = models.EmailField("Adresse e-mail", unique=True)
    label = models.CharField("Libellé", max_length=120, blank=True, help_text="Ex. Secrétariat, Maire, Service communication")
    is_active = models.BooleanField("Recevoir les messages", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["email"]
        verbose_name = "Destinataire des contacts"
        verbose_name_plural = "Destinataires des contacts"

    def __str__(self):
        return f"{self.label} — {self.email}" if self.label else self.email


class ContactMessage(models.Model):
    name = models.CharField("Nom", max_length=160)
    email = models.EmailField("E-mail")
    phone = models.CharField("Téléphone", max_length=60, blank=True)
    subject = models.CharField("Objet", max_length=200)
    message = models.TextField("Contenu")
    created_at = models.DateTimeField("Reçu le", auto_now_add=True)
    email_sent = models.BooleanField("E-mail envoyé", default=False)
    is_processed = models.BooleanField("Traité", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"

    def __str__(self):
        return f"{self.subject} — {self.name}"


class QuickLink(models.Model):
    title = models.CharField("Titre", max_length=120)
    description = models.CharField("Description", max_length=220, blank=True)
    icon = models.CharField("Icône", max_length=20, default="→")
    url = models.CharField("Lien", max_length=255, default="#")
    is_active = models.BooleanField("Actif", default=True)
    order = models.PositiveIntegerField("Ordre", default=100)
    class Meta: ordering = ["order", "title"]
    def __str__(self): return self.title


class News(models.Model):
    title = models.CharField("Titre", max_length=200)
    excerpt = models.TextField("Résumé", blank=True)
    body = models.TextField("Contenu", blank=True)
    image_url = models.URLField("Image historique (URL)", blank=True)
    image_1_src = models.TextField("Image 1", blank=True)
    image_2_src = models.TextField("Image 2", blank=True)
    image_3_src = models.TextField("Image 3", blank=True)
    published_at = models.DateField("Date de publication")
    is_published = models.BooleanField("Publiée", default=True)
    class Meta: ordering = ["-published_at"]
    def __str__(self): return self.title
    @property
    def gallery_images(self):
        images = [self.image_1_src, self.image_2_src, self.image_3_src]
        images = [img for img in images if img]
        if not images and self.image_url:
            images = [self.image_url]
        return images


class Project(models.Model):
    STATUS_CHOICES = [("done", "Réalisé"), ("ongoing", "En cours"), ("planned", "À venir")]
    title = models.CharField("Titre", max_length=200)
    category = models.CharField("Catégorie", max_length=100, blank=True)
    description = models.TextField("Description", blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="planned")
    progress = models.PositiveSmallIntegerField("Avancement (%)", default=0)
    budget = models.DecimalField("Budget FCFA", max_digits=18, decimal_places=0, null=True, blank=True)
    image_url = models.URLField("Image historique (URL)", blank=True)
    image_1_src = models.TextField("Image 1", blank=True)
    image_2_src = models.TextField("Image 2", blank=True)
    image_3_src = models.TextField("Image 3", blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_published = models.BooleanField("Publié", default=True)
    def __str__(self): return self.title
    @property
    def gallery_images(self):
        images = [self.image_1_src, self.image_2_src, self.image_3_src]
        images = [img for img in images if img]
        if not images and self.image_url:
            images = [self.image_url]
        return images


class MapLayer(models.Model):
    name = models.CharField("Nom", max_length=160)
    category = models.CharField("Catégorie", max_length=100, blank=True)
    description = models.TextField("Description", blank=True)
    color = models.CharField("Couleur", max_length=20, default="#f28c28")
    is_public = models.BooleanField("Visible sur la carte publique", default=True)
    is_default_visible = models.BooleanField("Visible au démarrage", default=True)
    display_fields = models.JSONField("Champs à afficher", default=list, blank=True)
    def __str__(self): return self.name


class MapFeature(models.Model):
    layer = models.ForeignKey(MapLayer, on_delete=models.CASCADE, related_name="features")
    properties = models.JSONField(default=dict)
    geometry = models.JSONField(default=dict)


class UrbanismLayer(models.Model):
    name = models.CharField("Nom de la couche", max_length=160, unique=True)
    display_fields = models.JSONField("Champs à afficher", default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name


class Parcel(models.Model):
    source_layer = models.CharField("Couche d'origine", max_length=160, blank=True, db_index=True)
    reference = models.CharField("Référence", max_length=120)
    section = models.CharField("Section", max_length=80, blank=True)
    ilot = models.CharField("Îlot", max_length=80, blank=True)
    lot = models.CharField("Lot", max_length=80, blank=True)
    parcel_number = models.CharField("N° parcelle", max_length=80, blank=True)
    area_m2 = models.DecimalField("Superficie m²", max_digits=14, decimal_places=2, null=True, blank=True)
    usage = models.CharField("Usage", max_length=120, blank=True)
    properties = models.JSONField(default=dict, blank=True)
    geometry = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_layer", "reference"], name="uniq_parcel_layer_reference")]
    def __str__(self): return f"{self.source_layer} - {self.reference}" if self.source_layer else self.reference


class MunicipalRevenueTheme(models.Model):
    FREQUENCY_CHOICES = [
        ("daily", "Quotidienne"),
        ("weekly", "Hebdomadaire"),
        ("monthly", "Mensuelle"),
    ]
    name = models.CharField("Thématique de recette", max_length=160, unique=True)
    description = models.TextField("Description", blank=True)
    frequency = models.CharField("Périodicité", max_length=20, choices=FREQUENCY_CHOICES, default="daily")
    target_amount = models.DecimalField("Objectif par période (FCFA)", max_digits=16, decimal_places=0, null=True, blank=True)
    is_active = models.BooleanField("Active", default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="municipal_revenue_themes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Thématique de collecte municipale"
        verbose_name_plural = "Thématiques de collecte municipale"

    def __str__(self):
        return self.name


class MunicipalRevenueEntry(models.Model):
    theme = models.ForeignKey(MunicipalRevenueTheme, on_delete=models.PROTECT, related_name="entries")
    collection_date = models.DateField("Date de collecte")
    amount = models.DecimalField("Montant collecté (FCFA)", max_digits=16, decimal_places=0)
    comment = models.TextField("Commentaire", blank=True)
    receipt_reference = models.CharField("Référence / quittance", max_length=120, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="municipal_revenue_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-collection_date", "-created_at"]
        verbose_name = "Collecte municipale"
        verbose_name_plural = "Collectes municipales"
        indexes = [
            models.Index(fields=["collection_date"], name="portal_muni_collect_2837f4_idx"),
            models.Index(fields=["theme", "collection_date"], name="portal_muni_theme_i_2992e1_idx"),
        ]

    def __str__(self):
        return f"{self.theme} - {self.collection_date} - {self.amount} FCFA"


class Taxpayer(models.Model):
    name = models.CharField("Nom / raison sociale", max_length=180)
    phone = models.CharField("Téléphone", max_length=60, blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    parcel = models.ForeignKey(Parcel, null=True, blank=True, on_delete=models.SET_NULL, related_name="taxpayers")
    def __str__(self): return self.name


class Tax(models.Model):
    STATUS_CHOICES = [("unpaid", "Impayée"), ("partial", "Partielle"), ("paid", "Payée")]
    taxpayer = models.ForeignKey(Taxpayer, on_delete=models.CASCADE, related_name="taxes")
    label = models.CharField("Type de taxe", max_length=160)
    year = models.PositiveIntegerField("Année")
    amount_due = models.DecimalField("Montant dû", max_digits=14, decimal_places=0)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="unpaid")
    def __str__(self): return f"{self.label} - {self.taxpayer}"


class Payment(models.Model):
    tax = models.ForeignKey(Tax, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField("Montant", max_digits=14, decimal_places=0)
    paid_at = models.DateField("Date de paiement")
    method = models.CharField("Mode de paiement", max_length=80, blank=True)
    reference = models.CharField("Référence", max_length=120, blank=True)
    def __str__(self): return f"{self.amount} FCFA - {self.tax}"
