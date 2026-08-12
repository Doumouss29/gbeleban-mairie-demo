import base64
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .models import ProjectPilotage, ProjectStep

User = get_user_model()


def _date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _percent(value):
    try:
        return max(0, min(100, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _image_data(uploaded):
    if not uploaded:
        return None
    if uploaded.size > 3 * 1024 * 1024:
        raise ValueError("L'image doit faire moins de 3 Mo.")
    mime = uploaded.content_type or "image/jpeg"
    if not mime.startswith("image/"):
        raise ValueError("Le fichier sélectionné n'est pas une image.")
    return f"data:{mime};base64,{base64.b64encode(uploaded.read()).decode('ascii')}"


def _visible_projects(user):
    qs = ProjectPilotage.objects.prefetch_related("members", "steps")
    if user.is_staff or user.is_superuser:
        return qs
    return qs.filter(Q(members=user) | Q(created_by=user)).distinct()


def _project_for_user(user, project_id):
    return get_object_or_404(_visible_projects(user), pk=project_id)


@login_required
def dashboard(request):
    can_admin = request.user.is_staff or request.user.is_superuser

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "create_project":
            if not can_admin:
                messages.error(request, "Seuls les responsables habilités peuvent créer un projet.")
                return redirect("pilotage:dashboard")
            title = request.POST.get("title", "").strip()
            if not title:
                messages.error(request, "Le nom du projet est obligatoire.")
                return redirect("pilotage:dashboard")
            try:
                image_src = _image_data(request.FILES.get("image")) or ""
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect("pilotage:dashboard")
            project = ProjectPilotage.objects.create(
                title=title,
                description=request.POST.get("description", "").strip(),
                image_src=image_src,
                status=request.POST.get("status", "planned"),
                progress=_percent(request.POST.get("progress")),
                budget_planned=_decimal(request.POST.get("budget_planned")),
                budget_spent=_decimal(request.POST.get("budget_spent")) or Decimal("0"),
                start_date=_date(request.POST.get("start_date")),
                end_date=_date(request.POST.get("end_date")),
                created_by=request.user,
            )
            member_ids = request.POST.getlist("members")
            members = User.objects.filter(is_active=True, id__in=member_ids)
            project.members.set(members)
            project.members.add(request.user)
            messages.success(request, f"Projet « {project.title} » créé.")
            return redirect(f"/pilotage-projets/?project={project.id}")

        project_id = request.POST.get("project_id")
        project = _project_for_user(request.user, project_id)
        is_owner = can_admin or project.created_by_id == request.user.id

        if action == "update_project":
            project.title = request.POST.get("title", project.title).strip() or project.title
            project.description = request.POST.get("description", "").strip()
            project.status = request.POST.get("status", project.status)
            project.progress = _percent(request.POST.get("progress"))
            project.budget_planned = _decimal(request.POST.get("budget_planned"))
            project.budget_spent = _decimal(request.POST.get("budget_spent")) or Decimal("0")
            project.start_date = _date(request.POST.get("start_date"))
            project.end_date = _date(request.POST.get("end_date"))
            if request.FILES.get("image"):
                try:
                    project.image_src = _image_data(request.FILES.get("image"))
                except ValueError as exc:
                    messages.error(request, str(exc))
                    return redirect(f"/pilotage-projets/?project={project.id}")
            project.save()
            messages.success(request, "Projet mis à jour.")

        elif action == "update_members":
            if not is_owner:
                messages.error(request, "Vous ne pouvez pas modifier l'équipe de ce projet.")
                return redirect(f"/pilotage-projets/?project={project.id}")
            members = User.objects.filter(is_active=True, id__in=request.POST.getlist("members"))
            project.members.set(members)
            if project.created_by:
                project.members.add(project.created_by)
            messages.success(request, "Équipe projet mise à jour.")

        elif action == "add_step":
            responsible_id = request.POST.get("responsible") or None
            responsible = User.objects.filter(id=responsible_id, is_active=True).first() if responsible_id else None
            ProjectStep.objects.create(
                project=project,
                title=request.POST.get("title", "Nouvelle étape").strip() or "Nouvelle étape",
                description=request.POST.get("description", "").strip(),
                status=request.POST.get("status", "todo"),
                progress=_percent(request.POST.get("progress")),
                start_date=_date(request.POST.get("start_date")),
                end_date=_date(request.POST.get("end_date")),
                budget=_decimal(request.POST.get("budget")),
                responsible=responsible,
                order=int(request.POST.get("order") or 100),
            )
            messages.success(request, "Étape ajoutée au planning.")

        elif action == "update_step":
            step = get_object_or_404(ProjectStep, pk=request.POST.get("step_id"), project=project)
            step.title = request.POST.get("title", step.title).strip() or step.title
            step.description = request.POST.get("description", "").strip()
            step.status = request.POST.get("status", step.status)
            step.progress = _percent(request.POST.get("progress"))
            step.start_date = _date(request.POST.get("start_date"))
            step.end_date = _date(request.POST.get("end_date"))
            step.budget = _decimal(request.POST.get("budget"))
            step.order = int(request.POST.get("order") or step.order)
            responsible_id = request.POST.get("responsible") or None
            step.responsible = User.objects.filter(id=responsible_id, is_active=True).first() if responsible_id else None
            step.save()
            messages.success(request, "Étape mise à jour.")

        elif action == "delete_step":
            step = get_object_or_404(ProjectStep, pk=request.POST.get("step_id"), project=project)
            if is_owner:
                step.delete()
                messages.success(request, "Étape supprimée.")

        return redirect(f"/pilotage-projets/?project={project.id}")

    projects = _visible_projects(request.user)
    selected_id = request.GET.get("project")
    selected = projects.filter(pk=selected_id).first() if selected_id else projects.first()
    users = User.objects.filter(is_active=True).order_by("first_name", "last_name", "username")
    return render(request, "pilotage/dashboard.html", {
        "projects": projects,
        "selected": selected,
        "users": users,
        "can_admin": can_admin,
    })
