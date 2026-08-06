import calendar
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseForbidden

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from .models import MunicipalRevenueEntry, MunicipalRevenueTheme


DASHBOARD_GROUP = "Accès Dashboard"


def _has_access(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=DASHBOARD_GROUP).exists())


def _parse_date(value, fallback):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date() if value else fallback
    except (TypeError, ValueError):
        return fallback


def _period_count(start_date, end_date, frequency):
    if end_date < start_date:
        return 0
    if frequency == "daily":
        return (end_date - start_date).days + 1
    if frequency == "weekly":
        return ((end_date - start_date).days // 7) + 1
    if frequency == "monthly":
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
    return 0


def _fmt_fcfa(value):
    try:
        return f"{Decimal(value):,.0f} FCFA".replace(",", " ")
    except Exception:
        return "0 FCFA"


@login_required
def dashboard_pdf(request):
    if not _has_access(request.user):
        return HttpResponseForbidden("Accès refusé")

    today = date.today()
    default_start = today.replace(day=1)
    default_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    start_date = _parse_date(request.GET.get("start"), default_start)
    end_date = _parse_date(request.GET.get("end"), default_end)
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    selected_theme = request.GET.get("theme", "").strip()
    entries = MunicipalRevenueEntry.objects.select_related("theme", "entered_by").filter(
        collection_date__range=(start_date, end_date)
    )
    themes = MunicipalRevenueTheme.objects.all()
    target_themes = themes.filter(is_active=True)
    if selected_theme:
        entries = entries.filter(theme_id=selected_theme)
        target_themes = target_themes.filter(id=selected_theme)

    collected = entries.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    objective = Decimal("0")
    for theme in target_themes:
        if theme.target_amount:
            objective += theme.target_amount * _period_count(start_date, end_date, theme.frequency)
    remaining = max(objective - collected, Decimal("0")) if objective else Decimal("0")
    rate = float(collected / objective * 100) if objective else 0

    by_theme = list(entries.values("theme__name").annotate(total=Sum("amount")).order_by("theme__name"))
    by_agent = list(
        entries.values("entered_by__username", "entered_by__first_name", "entered_by__last_name")
        .annotate(total=Sum("amount"))
        .order_by("entered_by__username")
    )

    selected_theme_name = "Toutes les thématiques"
    if selected_theme:
        selected_theme_name = themes.filter(id=selected_theme).values_list("name", flat=True).first() or "Thématique sélectionnée"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Rapport des recettes municipales - Gbéléban",
        author="Mairie de Gbéléban",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MunicipalTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18,
        leading=22, textColor=colors.HexColor("#056b3c"), alignment=TA_CENTER, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "MunicipalSub", parent=styles["Normal"], fontName="Helvetica", fontSize=9,
        leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=10,
    )
    heading = ParagraphStyle(
        "MunicipalHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12,
        leading=15, textColor=colors.HexColor("#173d2f"), spaceBefore=8, spaceAfter=6,
    )
    small = ParagraphStyle("Small", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=9.5)

    story = [
        Paragraph("MAIRIE DE GBÉLÉBAN", title_style),
        Paragraph("Rapport de suivi des recettes municipales", title_style),
        Paragraph(
            f"Période : {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Thématique : {selected_theme_name} &nbsp;&nbsp;|&nbsp;&nbsp; Édité le {today.strftime('%d/%m/%Y')}",
            subtitle_style,
        ),
    ]

    kpi_data = [
        ["Objectif théorique", "Montant collecté", "Écart à l'objectif", "Taux de réalisation", "Lignes de collecte"],
        [_fmt_fcfa(objective), _fmt_fcfa(collected), _fmt_fcfa(remaining), f"{rate:.1f} %", str(entries.count())],
    ]
    kpi_table = Table(kpi_data, colWidths=[52 * mm, 52 * mm, 52 * mm, 42 * mm, 42 * mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173d2f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f5f1ea")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7d7d7")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [kpi_table, Spacer(1, 7 * mm)]

    story.append(Paragraph("Recettes par thématique", heading))
    theme_data = [["Thématique", "Montant collecté"]]
    for row in by_theme:
        theme_data.append([row["theme__name"], _fmt_fcfa(row["total"])])
    if len(theme_data) == 1:
        theme_data.append(["Aucune donnée", "0 FCFA"])
    theme_table = Table(theme_data, colWidths=[150 * mm, 70 * mm])
    theme_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ef7d00")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7d7d7")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [theme_table, Spacer(1, 5 * mm)]

    story.append(Paragraph("Répartition par agent de saisie", heading))
    agent_data = [["Agent", "Montant saisi"]]
    for row in by_agent:
        full_name = " ".join(filter(None, [row["entered_by__first_name"], row["entered_by__last_name"]])).strip()
        agent = full_name or row["entered_by__username"] or "Compte supprimé / non renseigné"
        agent_data.append([agent, _fmt_fcfa(row["total"])])
    if len(agent_data) == 1:
        agent_data.append(["Aucune donnée", "0 FCFA"])
    agent_table = Table(agent_data, colWidths=[150 * mm, 70 * mm])
    agent_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#056b3c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7d7d7")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [agent_table, PageBreak()]

    story.append(Paragraph("Détail des collectes", heading))
    detail_data = [["Date", "Thématique", "Montant", "Agent", "Référence", "Commentaire"]]
    for entry in entries.order_by("collection_date", "theme__name", "created_at"):
        if entry.entered_by:
            agent = entry.entered_by.get_full_name().strip() or entry.entered_by.username
        else:
            agent = "—"
        detail_data.append([
            entry.collection_date.strftime("%d/%m/%Y"),
            Paragraph(entry.theme.name, small),
            _fmt_fcfa(entry.amount),
            Paragraph(agent, small),
            Paragraph(entry.receipt_reference or "—", small),
            Paragraph((entry.comment or "—")[:180], small),
        ])
    if len(detail_data) == 1:
        detail_data.append(["—", "Aucune collecte", "0 FCFA", "—", "—", "—"])

    detail_table = Table(detail_data, repeatRows=1, colWidths=[24*mm, 52*mm, 34*mm, 40*mm, 38*mm, 75*mm])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173d2f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7d7d7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf9f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(detail_table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    filename = f"rapport_recettes_gbeleban_{start_date.isoformat()}_{end_date.isoformat()}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
