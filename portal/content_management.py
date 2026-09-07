from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NewsManagementForm, ProjectManagementForm
from .models import News, Project


@staff_member_required
def news_management(request, news_id=None):
    instance = get_object_or_404(News, pk=news_id) if news_id else None
    form = NewsManagementForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        item = form.save()
        messages.success(
            request,
            f"Actualité « {item.title} » {'mise à jour' if instance else 'créée'} avec succès.",
        )
        return redirect("management_news")

    return render(
        request,
        "portal/management_news.html",
        {
            "form": form,
            "editing": instance,
            "news_items": News.objects.all()[:50],
        },
    )


@staff_member_required
def news_delete(request, news_id):
    item = get_object_or_404(News, pk=news_id)
    if request.method == "POST":
        title = item.title
        item.delete()
        messages.success(request, f"Actualité « {title} » supprimée.")
    return redirect("management_news")


@staff_member_required
def project_management(request, project_id=None):
    instance = get_object_or_404(Project, pk=project_id) if project_id else None
    form = ProjectManagementForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        item = form.save()
        messages.success(
            request,
            f"Projet « {item.title} » {'mis à jour' if instance else 'créé'} avec succès.",
        )
        return redirect("management_projects")

    return render(
        request,
        "portal/management_projects.html",
        {
            "form": form,
            "editing": instance,
            "projects": Project.objects.all().order_by("-id")[:50],
        },
    )


@staff_member_required
def project_delete(request, project_id):
    item = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        title = item.title
        item.delete()
        messages.success(request, f"Projet « {title} » supprimé.")
    return redirect("management_projects")
