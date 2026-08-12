from django.contrib import admin
from .models import ProjectPilotage, ProjectStep


class ProjectStepInline(admin.TabularInline):
    model = ProjectStep
    extra = 0
    fields = ("order", "title", "status", "progress", "responsible", "start_date", "end_date", "budget")


@admin.register(ProjectPilotage)
class ProjectPilotageAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "progress", "budget_planned", "budget_spent", "start_date", "end_date", "updated_at")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("title", "description")
    filter_horizontal = ("members",)
    inlines = (ProjectStepInline,)


@admin.register(ProjectStep)
class ProjectStepAdmin(admin.ModelAdmin):
    list_display = ("project", "order", "title", "status", "progress", "responsible", "start_date", "end_date", "budget")
    list_filter = ("status", "project")
    search_fields = ("title", "description", "project__title")
