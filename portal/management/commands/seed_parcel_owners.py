import base64
import csv
import gzip
import io
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from portal.models import Parcel
from portal.registry_models import ParcelOwner, ParcelOwnership


LEGAL_MARKERS = (
    "FAMILLE", "MAIRIE", "CGE", "SODECI", "FINANCEMENT", "LOGEMENT", "ETAT",
    "ÉTAT", "SOCIETE", "SOCIÉTÉ", "ASSOCIATION", "COOPERATIVE", "COOPÉRATIVE",
    "EGLISE", "ÉGLISE", "MOSQUEE", "MOSQUÉE", "MARCHE", "MARCHÉ", "ECOLE", "ÉCOLE",
)


def clean(value):
    return (value or "").strip()


def norm(value):
    return clean(value).casefold()


def is_legal(name):
    upper = clean(name).upper()
    return any(marker in upper for marker in LEGAL_MARKERS)


def owner_key(person_type, name):
    return person_type, norm(name)


class Command(BaseCommand):
    help = "Importe rapidement et de façon idempotente les propriétaires du GUIDE GBELEBAN."

    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parents[2] / "data" / "gbeleban_guide_owners.csv.gz.b64"
        if not data_path.exists():
            self.stdout.write(self.style.WARNING("Guide propriétaires absent : import ignoré."))
            return

        self.stdout.write("Chargement du guide propriétaires...")
        raw = gzip.decompress(base64.b64decode(data_path.read_text(encoding="utf-8"))).decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(raw)))

        # Une seule lecture SQL des parcelles au lieu de milliers de requêtes.
        parcels = list(Parcel.objects.only("id", "lot", "ilot"))
        exact_parcels = {}
        by_lot = {}
        for parcel in parcels:
            lot_key = norm(parcel.lot)
            ilot_key = norm(parcel.ilot)
            if not lot_key:
                continue
            by_lot.setdefault(lot_key, parcel)
            exact_parcels.setdefault((ilot_key, lot_key), parcel)

        prepared = []
        matched = 0
        skipped = 0
        for row in rows:
            lot = norm(row.get("lot"))
            ilot = norm(row.get("ilot"))
            if not lot:
                continue
            parcel = exact_parcels.get((ilot, lot)) if ilot else None
            parcel = parcel or by_lot.get(lot)
            if not parcel:
                skipped += 1
                continue
            matched += 1

            acquirers = [clean(row.get(f"acquirer_{i}")) for i in (1, 2, 3)]
            acquirers = [name for name in acquirers if name]
            entries = []
            landowner = clean(row.get("landowner"))
            if landowner:
                entries.append((landowner, "landowner", not bool(acquirers)))
            entries.extend((name, "acquirer", True) for name in acquirers)

            for name, role, current in entries:
                person_type = "legal" if is_legal(name) else "physical"
                prepared.append({
                    "parcel": parcel,
                    "person_type": person_type,
                    "name": name,
                    "role": role,
                    "current": current,
                    "address": clean(row.get("address")),
                    "representative": clean(row.get("family_representative")),
                    "reference": f"Guide #{clean(row.get('guide_no'))}",
                })

        self.stdout.write(f"Rapprochement terminé : {matched} lots trouvés, {skipped} sans correspondance.")

        # Une seule lecture SQL des propriétaires existants.
        existing_owners = list(ParcelOwner.objects.all())
        owners_by_key = {}
        for owner in existing_owners:
            name = owner.legal_name if owner.person_type == "legal" else owner.last_name
            if name:
                owners_by_key.setdefault(owner_key(owner.person_type, name), owner)

        missing = {}
        owners_to_update = {}
        for item in prepared:
            key = owner_key(item["person_type"], item["name"])
            owner = owners_by_key.get(key)
            if owner:
                changed = False
                if not owner.address and item["address"]:
                    owner.address = item["address"]
                    changed = True
                if not owner.representative_name and item["representative"]:
                    owner.representative_name = item["representative"]
                    changed = True
                if changed:
                    owners_to_update[owner.pk] = owner
                continue
            if key not in missing:
                owner = ParcelOwner(
                    person_type=item["person_type"],
                    address=item["address"],
                    representative_name=item["representative"],
                    notes="Import initial depuis le GUIDE GBELEBAN. Informations à compléter et valider.",
                )
                if item["person_type"] == "legal":
                    owner.legal_name = item["name"]
                else:
                    owner.last_name = item["name"]
                missing[key] = owner

        with transaction.atomic():
            if missing:
                ParcelOwner.objects.bulk_create(list(missing.values()), batch_size=500)
                owners_by_key.update(missing)
            if owners_to_update:
                ParcelOwner.objects.bulk_update(
                    list(owners_to_update.values()),
                    ["address", "representative_name", "updated_at"],
                    batch_size=500,
                )

            # Une seule lecture SQL des droits existants, puis insertion en masse.
            existing_rights = set(
                ParcelOwnership.objects.filter(source="GUIDE GBELEBAN").values_list(
                    "parcel_id", "owner_id", "role", "source_reference"
                )
            )
            rights = []
            seen = set(existing_rights)
            for item in prepared:
                owner = owners_by_key[owner_key(item["person_type"], item["name"])]
                key = (item["parcel"].id, owner.id, item["role"], item["reference"])
                if key in seen:
                    continue
                seen.add(key)
                rights.append(ParcelOwnership(
                    parcel=item["parcel"],
                    owner=owner,
                    role=item["role"],
                    source="GUIDE GBELEBAN",
                    source_reference=item["reference"],
                    is_current=item["current"],
                    notes="Statut issu du guide communal ; dates de propriété non renseignées dans la source.",
                ))
            if rights:
                ParcelOwnership.objects.bulk_create(rights, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"Guide propriétaires : {matched} lots rapprochés, {len(missing)} propriétaires créés, "
            f"{len(rights)} droits créés, {skipped} lots sans correspondance cadastrale."
        ))
