from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .models import Parcel
from .registry_models import ParcelOwner, ParcelOwnership

URBANISM_GROUP = "Accès Urbanisme"
MAX_IDENTITY_FILE_SIZE = 8 * 1024 * 1024
ALLOWED_IDENTITY_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


def _allowed(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=URBANISM_GROUP).exists())


def _forbidden():
    return JsonResponse({"detail": "Accès refusé"}, status=403)


def _date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _decimal(value):
    value = (value or "").strip().replace(",", ".")
    if not value:
        return None
    try:
        number = Decimal(value)
        if number < 0 or number > 100:
            return None
        return number
    except (InvalidOperation, ValueError):
        return None


def _owner_payload(owner):
    return {
        "id": owner.id,
        "person_type": owner.person_type,
        "display_name": owner.display_name,
        "last_name": owner.last_name,
        "first_names": owner.first_names,
        "birth_date": owner.birth_date.isoformat() if owner.birth_date else "",
        "birth_place": owner.birth_place,
        "nationality": owner.nationality,
        "profession": owner.profession,
        "legal_name": owner.legal_name,
        "legal_form": owner.legal_form,
        "registration_number": owner.registration_number,
        "tax_number": owner.tax_number,
        "representative_name": owner.representative_name,
        "representative_function": owner.representative_function,
        "phone": owner.phone,
        "email": owner.email,
        "address": owner.address,
        "identity_type": owner.identity_type,
        "identity_number": owner.identity_number,
        "identity_document_name": owner.identity_document_name,
        "identity_document_url": reverse("parcel_owner_identity", kwargs={"owner_id": owner.id}) if owner.identity_document_data else "",
        "notes": owner.notes,
    }


def _ownership_payload(record):
    return {
        "id": record.id,
        "owner": _owner_payload(record.owner),
        "role": record.role,
        "role_label": record.get_role_display(),
        "share_percentage": float(record.share_percentage) if record.share_percentage is not None else None,
        "start_date": record.start_date.isoformat() if record.start_date else "",
        "end_date": record.end_date.isoformat() if record.end_date else "",
        "is_current": record.is_current,
        "source": record.source,
        "source_reference": record.source_reference,
        "notes": record.notes,
    }


def _parcel_payload(parcel):
    records = list(parcel.ownership_records.select_related("owner").all())
    current = [r for r in records if r.is_current]
    return {
        "parcel": {
            "id": parcel.id,
            "couche": parcel.source_layer,
            "reference": parcel.reference,
            "section": parcel.section,
            "ilot": parcel.ilot,
            "lot": parcel.lot,
            "parcelle": parcel.parcel_number,
            "superficie": float(parcel.area_m2) if parcel.area_m2 is not None else None,
            "usage": parcel.usage,
            "properties": parcel.properties or {},
        },
        "current_owners": [_ownership_payload(r) for r in current],
        "history": [_ownership_payload(r) for r in records],
    }


def _fill_owner(owner, request):
    data = request.POST
    owner.person_type = data.get("person_type", owner.person_type or ParcelOwner.PERSON_TYPE_PHYSICAL)
    if owner.person_type not in dict(ParcelOwner.PERSON_TYPE_CHOICES):
        owner.person_type = ParcelOwner.PERSON_TYPE_PHYSICAL

    owner.last_name = data.get("last_name", "").strip()
    owner.first_names = data.get("first_names", "").strip()
    owner.birth_date = _date(data.get("birth_date"))
    owner.birth_place = data.get("birth_place", "").strip()
    owner.nationality = data.get("nationality", "").strip()
    owner.profession = data.get("profession", "").strip()

    owner.legal_name = data.get("legal_name", "").strip()
    owner.legal_form = data.get("legal_form", "").strip()
    owner.registration_number = data.get("registration_number", "").strip()
    owner.tax_number = data.get("tax_number", "").strip()
    owner.representative_name = data.get("representative_name", "").strip()
    owner.representative_function = data.get("representative_function", "").strip()

    owner.phone = data.get("phone", "").strip()
    owner.email = data.get("email", "").strip()
    owner.address = data.get("address", "").strip()
    owner.identity_type = data.get("identity_type", "").strip()
    owner.identity_number = data.get("identity_number", "").strip()
    owner.notes = data.get("owner_notes", data.get("notes", "")).strip()

    document = request.FILES.get("identity_document")
    if document:
        if document.size > MAX_IDENTITY_FILE_SIZE:
            raise ValueError("La pièce d'identité ne doit pas dépasser 8 Mo.")
        content_type = document.content_type or "application/octet-stream"
        if content_type not in ALLOWED_IDENTITY_TYPES:
            raise ValueError("Format de pièce non autorisé. Utilisez PDF, JPG, PNG ou WEBP.")
        owner.identity_document_name = document.name[:255]
        owner.identity_document_type = content_type[:120]
        owner.identity_document_data = document.read()

    if owner.person_type == ParcelOwner.PERSON_TYPE_LEGAL:
        if not owner.legal_name:
            raise ValueError("La raison sociale est obligatoire pour une personne morale.")
    else:
        if not owner.last_name:
            raise ValueError("Le nom est obligatoire pour une personne physique.")


@login_required
@require_http_methods(["GET"])
def parcel_record(request, parcel_id):
    if not _allowed(request.user):
        return _forbidden()
    parcel = get_object_or_404(Parcel, pk=parcel_id)
    return JsonResponse(_parcel_payload(parcel))


@login_required
@require_POST
def parcel_add_owner(request, parcel_id):
    if not _allowed(request.user):
        return _forbidden()
    parcel = get_object_or_404(Parcel, pk=parcel_id)
    mode = request.POST.get("mode", "add")
    if mode not in {"add", "replace"}:
        mode = "add"

    try:
        with transaction.atomic():
            owner = ParcelOwner(created_by=request.user)
            _fill_owner(owner, request)
            owner.save()

            start_date = _date(request.POST.get("start_date"))
            if mode == "replace":
                close_date = (start_date - timedelta(days=1)) if start_date else datetime.now().date()
                ParcelOwnership.objects.filter(parcel=parcel, is_current=True).update(is_current=False, end_date=close_date)

            role = request.POST.get("role", "owner")
            if role not in dict(ParcelOwnership.ROLE_CHOICES):
                role = "owner"
            ParcelOwnership.objects.create(
                parcel=parcel,
                owner=owner,
                role=role,
                share_percentage=_decimal(request.POST.get("share_percentage")),
                start_date=start_date,
                is_current=True,
                source=request.POST.get("source", "Saisie Urbanisme").strip(),
                source_reference=request.POST.get("source_reference", "").strip(),
                notes=request.POST.get("ownership_notes", "").strip(),
                created_by=request.user,
            )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    return JsonResponse(_parcel_payload(parcel), status=201)


@login_required
@require_POST
def parcel_owner_update(request, owner_id):
    if not _allowed(request.user):
        return _forbidden()
    owner = get_object_or_404(ParcelOwner, pk=owner_id)
    try:
        _fill_owner(owner, request)
        owner.save()
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse({"owner": _owner_payload(owner)})


@login_required
@require_POST
def parcel_ownership_update(request, ownership_id):
    if not _allowed(request.user):
        return _forbidden()
    record = get_object_or_404(ParcelOwnership.objects.select_related("owner", "parcel"), pk=ownership_id)
    role = request.POST.get("role", record.role)
    if role in dict(ParcelOwnership.ROLE_CHOICES):
        record.role = role
    record.share_percentage = _decimal(request.POST.get("share_percentage"))
    record.start_date = _date(request.POST.get("start_date"))
    record.end_date = _date(request.POST.get("end_date"))
    record.is_current = request.POST.get("is_current", "true").lower() in {"true", "1", "on", "yes"}
    if record.end_date:
        record.is_current = False
    record.source = request.POST.get("source", record.source).strip()
    record.source_reference = request.POST.get("source_reference", record.source_reference).strip()
    record.notes = request.POST.get("ownership_notes", record.notes).strip()
    record.save()
    return JsonResponse(_parcel_payload(record.parcel))


@login_required
@require_http_methods(["GET"])
def parcel_owner_identity(request, owner_id):
    if not _allowed(request.user):
        return _forbidden()
    owner = get_object_or_404(ParcelOwner, pk=owner_id)
    if not owner.identity_document_data:
        return JsonResponse({"detail": "Aucune pièce d'identité enregistrée."}, status=404)
    response = HttpResponse(bytes(owner.identity_document_data), content_type=owner.identity_document_type or "application/octet-stream")
    filename = owner.identity_document_name or f"piece-identite-{owner.id}"
    response["Content-Disposition"] = f'inline; filename="{filename.replace(chr(34), "")}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
