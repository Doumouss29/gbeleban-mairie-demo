import base64
import csv
import gzip
import io
from pathlib import Path

from django.core.management.base import BaseCommand

from portal.models import Parcel
from portal.registry_models import ParcelOwner, ParcelOwnership


LEGAL_MARKERS = (
    "FAMILLE", "MAIRIE", "CGE", "SODECI", "FINANCEMENT", "LOGEMENT", "ETAT",
    "ÉTAT", "SOCIETE", "SOCIÉTÉ", "ASSOCIATION", "COOPERATIVE", "COOPÉRATIVE",
    "EGLISE", "ÉGLISE", "MOSQUEE", "MOSQUÉE", "MARCHE", "MARCHÉ", "ECOLE", "ÉCOLE",
)


def clean(value):
    return (value or "").strip()


def is_legal(name):
    upper=clean(name).upper()
    return any(marker in upper for marker in LEGAL_MARKERS)


class Command(BaseCommand):
    help = "Importe de façon idempotente les propriétaires du fichier GUIDE GBELEBAN dans le registre cadastral."

    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parents[2] / "data" / "gbeleban_guide_owners.csv.gz.b64"
        if not data_path.exists():
            self.stdout.write(self.style.WARNING("Guide propriétaires absent : import ignoré."))
            return

        raw = gzip.decompress(base64.b64decode(data_path.read_text(encoding="utf-8"))).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(raw))
        created_rights = 0
        matched = 0
        skipped = 0

        for row in reader:
            lot = clean(row.get("lot"))
            ilot = clean(row.get("ilot"))
            if not lot:
                continue

            qs = Parcel.objects.filter(lot__iexact=lot)
            if ilot:
                exact = qs.filter(ilot__iexact=ilot).first()
                parcel = exact or qs.first()
            else:
                parcel = qs.first()
            if not parcel:
                skipped += 1
                continue
            matched += 1

            acquirers = [clean(row.get(f"acquirer_{i}")) for i in (1,2,3)]
            acquirers = [name for name in acquirers if name]
            entries = []
            landowner = clean(row.get("landowner"))
            if landowner:
                entries.append((landowner, "landowner", not bool(acquirers)))
            for name in acquirers:
                entries.append((name, "acquirer", True))

            for name, role, current in entries:
                legal = is_legal(name)
                lookup = {"person_type": "legal", "legal_name__iexact": name} if legal else {"person_type": "physical", "last_name__iexact": name}
                owner = ParcelOwner.objects.filter(**lookup).first()
                if not owner:
                    owner = ParcelOwner(person_type="legal" if legal else "physical")
                    if legal:
                        owner.legal_name = name
                    else:
                        owner.last_name = name
                    owner.address = clean(row.get("address"))
                    owner.representative_name = clean(row.get("family_representative"))
                    owner.notes = "Import initial depuis le GUIDE GBELEBAN. Informations à compléter et valider."
                    owner.save()
                else:
                    changed = False
                    if not owner.address and clean(row.get("address")):
                        owner.address = clean(row.get("address")); changed=True
                    if not owner.representative_name and clean(row.get("family_representative")):
                        owner.representative_name = clean(row.get("family_representative")); changed=True
                    if changed:
                        owner.save()

                ref = f"Guide #{clean(row.get('guide_no'))}"
                _, created = ParcelOwnership.objects.get_or_create(
                    parcel=parcel,
                    owner=owner,
                    role=role,
                    source="GUIDE GBELEBAN",
                    source_reference=ref,
                    defaults={
                        "is_current": current,
                        "notes": "Statut issu du guide communal ; dates de propriété non renseignées dans la source.",
                    },
                )
                if created:
                    created_rights += 1

        self.stdout.write(self.style.SUCCESS(
            f"Guide propriétaires : {matched} lots rapprochés, {created_rights} droits créés, {skipped} lots sans correspondance cadastrale."
        ))
