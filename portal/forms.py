import base64
import json
from django import forms
from .models import SiteSettings, News, Project


def _image_to_data_uri(uploaded, max_mb=3):
    if not uploaded:
        return None
    if uploaded.size > max_mb * 1024 * 1024:
        raise forms.ValidationError(f"L'image doit faire moins de {max_mb} Mo.")
    mime = uploaded.content_type or "image/jpeg"
    if not mime.startswith("image/"):
        raise forms.ValidationError("Le fichier sélectionné n'est pas une image.")
    encoded = base64.b64encode(uploaded.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


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
                setattr(obj, model_field, _image_to_data_uri(uploaded))
        if commit:
            obj.save()
        return obj


class _ThreeImageAdminForm(forms.ModelForm):
    image_1_upload = forms.ImageField(label="Importer image 1", required=False)
    image_2_upload = forms.ImageField(label="Importer image 2", required=False)
    image_3_upload = forms.ImageField(label="Importer image 3", required=False)

    def save(self, commit=True):
        obj = super().save(commit=False)
        for idx in (1, 2, 3):
            uploaded = self.cleaned_data.get(f"image_{idx}_upload")
            if uploaded:
                setattr(obj, f"image_{idx}_src", _image_to_data_uri(uploaded))
        if commit:
            obj.save()
        return obj


class NewsAdminForm(_ThreeImageAdminForm):
    class Meta:
        model = News
        fields = "__all__"
        widgets = {
            "image_1_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez une image"}),
            "image_2_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez une image"}),
            "image_3_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez une image"}),
        }


class ProjectAdminForm(_ThreeImageAdminForm):
    class Meta:
        model = Project
        fields = "__all__"
        widgets = {
            "image_1_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez une image"}),
            "image_2_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez une image"}),
            "image_3_src": forms.TextInput(attrs={"placeholder": "URL ou laisser vide si vous importez une image"}),
        }


class GeoJSONImportForm(forms.Form):
    layer_name = forms.CharField(label="Nom de la couche", max_length=160)
    category = forms.CharField(label="Catégorie", max_length=100, required=False)
    color = forms.CharField(label="Couleur", initial="#ef7d00", max_length=20)
    is_public = forms.BooleanField(label="Visible sur la carte publique", initial=True, required=False)
    is_default_visible = forms.BooleanField(label="Visible au démarrage", initial=True, required=False)
    geojson_file = forms.FileField(label="Fichier GeoJSON")
    display_fields = forms.CharField(label="Champs à afficher", required=False, widget=forms.HiddenInput())

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
    reference_field = forms.CharField(label="Champ référence", required=False, widget=forms.Select())
    section_field = forms.CharField(label="Champ section", required=False, widget=forms.Select())
    ilot_field = forms.CharField(label="Champ îlot", required=False, widget=forms.Select())
    lot_field = forms.CharField(label="Champ lot", required=False, widget=forms.Select())
    parcel_field = forms.CharField(label="Champ parcelle", required=False, widget=forms.Select())
    area_field = forms.CharField(label="Champ superficie", required=False, widget=forms.Select())
    usage_field = forms.CharField(label="Champ usage", required=False, widget=forms.Select())
    display_fields = forms.CharField(label="Champs à afficher", required=False, widget=forms.HiddenInput())

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
