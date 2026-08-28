from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from .addressing import ADDRESS_LAYER, _filtered_address_queryset
from .models import Parcel


def _address_queryset():
    return Parcel.objects.filter(source_layer=ADDRESS_LAYER)


@staff_member_required
def delete_selected_addresses(request):
    if request.method != "POST":
        raise Http404

    if request.POST.get("all_filtered") == "1":
        qs = _filtered_address_queryset(
            request.POST.get("q", "").strip(),
            request.POST.get("status", "").strip(),
            request.POST.get("quality", "").strip(),
        )
    else:
        ids = [int(value) for value in request.POST.getlist("address_ids") if value.isdigit()]
        if not ids:
            messages.warning(request, "Aucune adresse sélectionnée.")
            return redirect("addressing_management")
        qs = _address_queryset().filter(id__in=ids)

    count = qs.count()
    qs.delete()
    messages.success(request, f"{count} adresse(s) supprimée(s).")
    return redirect("addressing_management")


@staff_member_required
def delete_address(request, parcel_id):
    if request.method != "POST":
        raise Http404

    parcel = get_object_or_404(_address_queryset(), pk=parcel_id)
    props = dict(parcel.properties or {})
    label = props.get("LIBELLE_ADR") or props.get("CODE_ADRESSE") or f"Îlot {parcel.ilot} / Lot {parcel.lot}"
    parcel.delete()
    messages.success(request, f"Adresse « {label} » supprimée.")
    return redirect("addressing_management")
