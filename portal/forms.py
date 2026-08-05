import base64
import json
from django import forms
from .models import SiteSettings


class SiteSettingsAdminForm(forms.ModelForm):
    municipality_logo_upload = forms.ImageField(label="Importer le logo / armoirie de la commune", required=False)
    national_arms_upload = forms.ImageField(label="Importer les armoiries de Côte d'Ivoire", required=False)
    hero_image_upload = forms.ImageField(label="Importer une image de couverture", required=False)
    mayor_hero_image_upload = forms.ImageField(label="Importer la photo du maire - bloc d'accueil", required=False)
    mayor_section_image_upload = forms.ImageField(label="Importer la photo du maire - section Le mot du Maire", required=False)

    class Meta:
        model = SiteSettings
        fields = "__all__"
        widgets = {
            "municipality_logo_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez un fichier"}),
            "national_arms_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez un fichier"}),
            "hero_image_url": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez un fichier"}),
            "mayor_hero_image_url": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez un fichier"}),
            "mayor_section_image_url": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez un fichier"}),
        }

    @staticmethod
    def _as_data_uri(uploaded):
        if not uploaded:
            return None
        if uploaded.size > 3 * 1024 * 1024:
            raise forms.ValidationError("L'image doit faire moins de 3 Mo pour cette version de démonstration.")
        mime = uploaded.content_type or "image/jpeg"
        if not mime.startswith("image/"):
            raise forms.ValidationError("Le fichier sélectionné n'est pas une image.")
        encoded = base64.b64encode(uploaded.read()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def save(self, commit=True):
        obj = super().save(commit=False)
        mapping = {
            "municipality_logo_upload": "municipality_logo_src",
            "national_arms_upload": "national_arms_src",
            "hero_image_upload": "hero_image_url",
            "mayor_hero_image_upload": "mayor_hero_image_url",
            "mayor_section_image_upload": "mayor_section_image_url",
        }
        for upload_field, model_field in mapping.items():
            uploaded = self.cleaned_data.get(upload_field)
            if uploaded:
                setattr(obj, model_field, self._as_data_uri(uploaded))
        if commit:
            obj.save()
        return obj


class GeoJSONImportForm(forms.Form):
    layer_name = forms.CharField(label="Nom de la couche", max_length=160)
    category = forms.CharField(label="Catégorie", max_length=100, required=False)
    color = forms.CharField(label="Couleur", initial="#ef7d00", max_length=20)
    is_public = forms.BooleanField(label="Visible sur la carte publique", initial=True, required=False)
    is_default_visible = forms.BooleanField(label="Visible au démarrage", initial=True, required=False)
    geojson_file = forms.FileField(label="Fichier GeoJSON")
    display_fields = forms.CharField(
        label="Champs à afficher",
        required=False,
        widget=forms.HiddenInput(),
        help_text="La liste est détectée automatiquement à partir du GeoJSON après sélection du fichier.",
    )

    def clean_display_fields(self):
        raw = self.cleaned_data.get("display_fields") or ""
        if not raw:
            return []
        try:
            value = json.loads(raw)
        except Exception:
            raise forms.ValidationError("La sélection des champs à afficher est invalide.")
        if not isinstance(value, list):
            raise forms.ValidationError("La sélection des champs à afficher est invalide.")
        return [str(v) for v in value if str(v).strip()]


class CadastreImportForm(forms.Form):
    layer_name = forms.CharField(label="Nom de la couche urbanisme", max_length=160)
    geojson_file = forms.FileField(label="Plan cadastral GeoJSON")
    reference_field = forms.CharField(label="Champ référence", initial="reference")
    section_field = forms.CharField(label="Champ section", initial="section", required=False)
    ilot_field = forms.CharField(label="Champ îlot", initial="ilot", required=False)
    lot_field = forms.CharField(label="Champ lot", initial="lot", required=False)
    parcel_field = forms.CharField(label="Champ parcelle", initial="parcelle", required=False)
    area_field = forms.CharField(label="Champ superficie", initial="superficie", required=False)
    usage_field = forms.CharField(label="Champ usage", initial="usage", required=False)
