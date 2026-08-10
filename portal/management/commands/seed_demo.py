from datetime import date
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from portal.models import SiteSettings, Page, QuickLink, News, MapLayer, Parcel, Taxpayer


class Command(BaseCommand):
    help = "Initialise uniquement les contenus structurels du portail et nettoie les anciennes données de démonstration."

    def handle(self, *args, **options):
        Group.objects.get_or_create(name="Accès Urbanisme")
        Group.objects.get_or_create(name="Accès Dashboard")
        Group.objects.get_or_create(name="Accès Collecte municipale")

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
            ("Nos projets", "Réalisés, en cours et à venir", "🏗️", "/projets/", 30),
            ("Gbéléban en carte", "Équipements et points d’intérêt", "📍", "/gbeleban-en-carte/", 40),
        ]:
            QuickLink.objects.get_or_create(title=title, defaults={"description": desc, "icon": icon, "url": url, "order": order})

        News.objects.get_or_create(
            title="La gestion municipale de Gbéléban saluée lors du Conseil municipal",
            defaults={
                "excerpt": "À l’occasion de la deuxième réunion du Conseil municipal de l’exercice 2026, la gestion de l’équipe municipale et les investissements engagés en faveur du développement de Gbéléban ont été salués.",
                "body": (
                    "Le samedi 6 juin 2026, le Sénateur du Kabadougou, Vassiriki Diaby, a pris part à la deuxième réunion du Conseil municipal de Gbéléban au titre de l’exercice 2026.\n\n"
                    "À l’issue des travaux, consacrés à l’examen des différents points inscrits à l’ordre du jour, il a exprimé sa satisfaction quant à la gestion de la municipalité et aux résultats des actions de développement conduites sous l’autorité de Madame Sita Ouattara, Maire de Gbéléban.\n\n"
                    "Le Sénateur a notamment mis en avant l’orientation du budget primitif 2026 : 13 % des ressources sont consacrées au fonctionnement, contre 87 % destinées aux investissements. Une répartition qu’il a présentée comme le signe d’une gestion rigoureuse et résolument tournée vers le développement de la commune.\n\n"
                    "Il a également rappelé le rôle du Sénat dans la représentation et le suivi des collectivités territoriales, soulignant à ce titre l’importance d’une gestion locale efficace et d’investissements visibles au bénéfice des populations.\n\n"
                    "Au cours des dernières années, la municipalité de Gbéléban a engagé plusieurs actions visant à renforcer les infrastructures de base, améliorer les équipements structurants et accompagner la transformation progressive de la commune. Ces réalisations participent à l’amélioration du cadre de vie et à l’attractivité du territoire.\n\n"
                    "Cette dynamique traduit l’ambition portée par l’équipe municipale : faire de Gbéléban une commune moderne, mieux équipée, attractive et tournée vers l’avenir.\n\n"
                    "Source : Sercom / lemeridien.ci"
                ),
                "published_at": date(2026, 6, 8),
                "is_published": True,
            }
        )

        News.objects.get_or_create(
            title="Gbéléban renforce son attractivité avec un programme de logements modernes",
            defaults={
                "excerpt": "La commune poursuit sa transformation avec un programme de logements destinés notamment aux fonctionnaires et agents affectés à Gbéléban, afin d’améliorer les conditions d’accueil et de renforcer l’attractivité du territoire.",
                "body": (
                    "Gbéléban poursuit sa dynamique de modernisation avec la réalisation de nouveaux logements destinés en priorité aux fonctionnaires et agents en poste dans la commune. Ce programme répond à un besoin concret : améliorer les conditions d’hébergement dans une localité frontalière où l’offre de logements adaptés a longtemps été limitée.\n\n"
                    "Une première phase porte sur vingt logements modernes de quatre pièces, comprenant trois chambres et un salon. Au 20 mai 2026, l’avancement des travaux était annoncé à environ 95 %, plaçant cette opération en phase finale de réalisation.\n\n"
                    "Au-delà du confort résidentiel, le projet poursuit un objectif plus large d’attractivité territoriale. En facilitant l’installation des agents de l’État et des personnels affectés à Gbéléban, la commune entend renforcer durablement la présence des services publics et améliorer le cadre de vie des personnes appelées à y travailler.\n\n"
                    "La programmation prévoit également quinze logements supplémentaires de trois pièces, puis une extension de cinq unités. À terme, l’ensemble du programme devrait ainsi dépasser quarante logements. Selon les informations communiquées au moment de l’annonce, la livraison des premiers logements était prévue à partir d’août 2026.\n\n"
                    "Cette opération s’inscrit dans le Plan triennal 2025-2026-2027 de la commune, avec une orientation centrée sur les infrastructures sociales, l’amélioration du cadre de vie et le renforcement de l’attractivité de Gbéléban. Elle illustre la volonté municipale de poursuivre une transformation urbaine progressive, associant équipements, habitat et amélioration des services à la population.\n\n"
                    "Source : Le Méridien, article publié le 20 mai 2026."
                ),
                "published_at": date(2026, 5, 20),
                "is_published": True,
            }
        )

        # Suppression définitive des anciennes données techniques de démonstration.
        # Ces suppressions sont volontairement ciblées afin de ne jamais toucher
        # les vraies données ajoutées depuis l'administration.
        demo_layers = MapLayer.objects.filter(name="Équipements de démonstration")
        deleted_layers = demo_layers.count()
        demo_layers.delete()

        deleted_parcels, _ = Parcel.objects.filter(reference__startswith="DEMO-").delete()

        demo_taxpayers = Taxpayer.objects.filter(name__startswith="Démonstration -")
        deleted_taxpayers = demo_taxpayers.count()
        demo_taxpayers.delete()

        if deleted_layers or deleted_parcels or deleted_taxpayers:
            self.stdout.write(self.style.WARNING(
                f"Nettoyage démo : {deleted_layers} couche(s), "
                f"{deleted_parcels} enregistrement(s) cadastral(aux), "
                f"{deleted_taxpayers} contribuable(s) supprimé(s)."
            ))

        self.stdout.write(self.style.SUCCESS("Initialisation du portail terminée — aucune donnée SIG de démonstration créée."))
