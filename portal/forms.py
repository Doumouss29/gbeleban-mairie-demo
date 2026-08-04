from django import forms

class GeoJSONImportForm(forms.Form):
    layer_name = forms.CharField(label="Nom de la couche", max_length=160)
    category = forms.CharField(label="Catégorie", max_length=100, required=False)
    color = forms.CharField(label="Couleur", initial="#ef7d00", max_length=20)
    is_public = forms.BooleanField(label="Visible sur la carte publique", initial=True, required=False)
    geojson_file = forms.FileField(label="Fichier GeoJSON")

class CadastreImportForm(forms.Form):
    geojson_file = forms.FileField(label="Plan cadastral GeoJSON")
    reference_field = forms.CharField(label="Champ référence", initial="reference")
    section_field = forms.CharField(label="Champ section", initial="section", required=False)
    ilot_field = forms.CharField(label="Champ îlot", initial="ilot", required=False)
    lot_field = forms.CharField(label="Champ lot", initial="lot", required=False)
    parcel_field = forms.CharField(label="Champ parcelle", initial="parcelle", required=False)
    area_field = forms.CharField(label="Champ superficie", initial="superficie", required=False)
    usage_field = forms.CharField(label="Champ usage", initial="usage", required=False)
