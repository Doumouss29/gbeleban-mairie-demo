from django.shortcuts import get_object_or_404, render

from .models import Project


def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id, is_published=True)
    return render(request, "portal/project_detail.html", {"project": project})
