from datetime import date
from decimal import Decimal
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from portal.models import SiteSettings, Page, QuickLink, News, Project, Taxpayer, Tax, Payment, MapLayer, MapFeature, Parcel


class Command(BaseCommand):
    help = "Ajoute les contenus de démonstration sans écraser les contenus existants."

    def handle(self, *args, **options):
        # Groupes fonctionnels utilisés pour piloter les accès applicatifs.
        Group.objects.get_or_create(name="Accès Urbanisme")
        Group.objects.get_or_create(name="Accès Dashboard")

        SiteSettings.objects.get_or_create(id=1, defaults={
            "municipality_name": "Commune de Gbéléban",
            "hero_title": "Bienvenue à Gbéléban",
            "hero_text": "Un portail municipal moderne pour informer les citoyens, valoriser le territoire, suivre les projets de la commune et faciliter l’accès aux services municipaux.",
            "mayor_name": "Madame le Maire",
            "mayor_message": "Une municipalité proche des habitants, engagée pour le développement local et la modernisation des services publics.",
        })

        for title, slug, order, summary, content in [
            ("La Commune", "la-commune", 10, "Découvrir Gbéléban, son histoire et son territoire.", "Gbéléban est une commune de Côte d'Ivoire. Cette page est modifiable depuis l'administration."),
            ("Démarches", "demarches", 60, "Informations et services municipaux.", "Ajoutez ici les démarches à proposer aux citoyens. Cette page peut être masquée ou remplacée."),
            ("Contact", "contact", 90, "Contacter la mairie.", "Renseignez ici les coordonnées, horaires et moyens de contact de la mairie."),
        ]:
            Page.objects.get_or_create(slug=slug, defaults={"title": title, "menu_order": order, "summary": summary, "content": content})

        for title, desc, icon, url, order in [
            ("Mes démarches", "État civil, demandes et informations utiles", "📄", "/pages/demarches/", 10),
            ("Nos projets", "Réalisés, en cours et à venir", "🏗️", "/projets/", 30),
            ("Gbéléban en carte", "Équipements et points d’intérêt", "📍", "/gbeleban-en-carte/", 40),
        ]:
            QuickLink.objects.get_or_create(title=title, defaults={"description": desc, "icon": icon, "url": url, "order": order})

        for title, category, status, progress, budget in [
            ("Réhabilitation d'une école primaire", "Éducation", "ongoing", 65, 45000000),
            ("Aménagement de voirie communale", "Voirie", "done", 100, 80000000),
            ("Projet de marché municipal", "Commerce", "planned", 0, 120000000),
        ]:
            Project.objects.get_or_create(title=title, defaults={
                "category": category, "status": status, "progress": progress, "budget": budget,
                "description": "Donnée de démonstration à remplacer par les informations officielles."
            })

        News.objects.get_or_create(
            title="Bienvenue sur le portail numérique de Gbéléban",
            defaults={"excerpt": "Découvrez les projets, services et informations de la commune.", "published_at": date.today()}
        )

        if not MapLayer.objects.exists():
            layer = MapLayer.objects.create(
                name="Équipements de démonstration", category="Services publics", color="#ef7d00",
                is_public=True, is_default_visible=True, display_fields=["nom", "type", "statut"]
            )
            for props, coords in [
                ({"nom": "Mairie de Gbéléban", "type": "Administration", "statut": "Démonstration"}, [-8.1318, 9.5846]),
                ({"nom": "École primaire - exemple", "type": "Éducation", "statut": "Démonstration"}, [-8.1289, 9.5863]),
                ({"nom": "Centre de santé - exemple", "type": "Santé", "statut": "Démonstration"}, [-8.1342, 9.5829]),
            ]:
                MapFeature.objects.create(layer=layer, properties=props, geometry={"type": "Point", "coordinates": coords})

        if not Parcel.objects.exists():
            for ref, section, ilot, lot, num, b in [
                ("DEMO-S01-I01-L01", "01", "01", "01", "1", [-8.1330, 9.5836, -8.1325, 9.5841]),
                ("DEMO-S01-I01-L02", "01", "01", "02", "2", [-8.1325, 9.5836, -8.1320, 9.5841]),
                ("DEMO-S01-I01-L03", "01", "01", "03", "3", [-8.1320, 9.5836, -8.1315, 9.5841]),
            ]:
                minx, miny, maxx, maxy = b
                geom = {"type": "Polygon", "coordinates": [[[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]]}
                Parcel.objects.create(reference=ref, section=section, ilot=ilot, lot=lot, parcel_number=num, area_m2=250, usage="Habitation", geometry=geom)

        if not Taxpayer.objects.exists():
            tp1 = Taxpayer.objects.create(name="Démonstration - Marché central", phone="0700000000")
            tp2 = Taxpayer.objects.create(name="Démonstration - Commerce A", phone="0500000000")
            t1 = Tax.objects.create(taxpayer=tp1, label="Taxe de marché", year=date.today().year, amount_due=Decimal("250000"), status="partial")
            t2 = Tax.objects.create(taxpayer=tp2, label="Taxe commerciale", year=date.today().year, amount_due=Decimal("180000"), status="paid")
            Payment.objects.create(tax=t1, amount=Decimal("150000"), paid_at=date.today(), method="Espèces", reference="DEMO-001")
            Payment.objects.create(tax=t2, amount=Decimal("180000"), paid_at=date.today(), method="Mobile Money", reference="DEMO-002")

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
