import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.ttfonts import TTFError
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _resource_path(*parts) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundled_path = Path(bundle_root, *parts)
        if bundled_path.exists():
            return bundled_path
    return Path(__file__).resolve().parents[1].joinpath(*parts)


def _register_font(alias: str, candidates: list[Path]):
    for path in candidates:
        if not path or not path.exists() or path.stat().st_size == 0:
            continue
        try:
            pdfmetrics.registerFont(TTFont(alias, str(path)))
            return alias
        except (OSError, TTFError):
            continue
    return None


def _select_fonts():
    fonts_dir = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "Fonts"
    regular_candidates = [
        _resource_path("fonts", "DejaVuSans.ttf"),
        fonts_dir / "arial.ttf",
    ]
    bold_candidates = [
        _resource_path("fonts", "DejaVuSans-Bold.ttf"),
        fonts_dir / "arialbd.ttf",
        _resource_path("fonts", "DejaVuSans.ttf"),
        fonts_dir / "arial.ttf",
    ]

    font_name = _register_font("AutoService-Regular", regular_candidates)
    font_name_bold = _register_font("AutoService-Bold", bold_candidates)
    return font_name or "Helvetica", font_name_bold or "Helvetica-Bold"


def _safe(value) -> str:
    return escape(str(value or ""))


def _money(value) -> str:
    return f"{float(value or 0):.2f}"


def _build_items_table(items, styles, col_widths):
    cell_center, cell_left, cell_right, th_center, th_left, th_right = styles
    table_data = [[
        Paragraph("<b>№</b>", th_center),
        Paragraph("<b>Назва</b>", th_left),
        Paragraph("<b>К-сть</b>", th_center),
        Paragraph("<b>Ціна</b>", th_right),
        Paragraph("<b>Сума</b>", th_right),
    ]]

    total = 0.0
    for index, item in enumerate(items, start=1):
        item_sum = float(item.get("sum", 0))
        table_data.append([
            Paragraph(str(index), cell_center),
            Paragraph(_safe(item.get("name")), cell_left),
            Paragraph(_safe(item.get("qty")), cell_center),
            Paragraph(_money(item.get("price")), cell_right),
            Paragraph(_money(item_sum), cell_right),
        ])
        total += item_sum

    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b4c7e")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table, total


def export_invoice(filename, vehicle, materials, works):
    font_name, font_name_bold = _select_fonts()

    pdf = SimpleDocTemplate(
        filename,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    col_widths = [10 * mm, 95 * mm, 20 * mm, 25 * mm, 30 * mm]
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName=font_name_bold,
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#2b4c7e"),
    )
    h2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Heading2"],
        fontName=font_name_bold,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2b4c7e"),
        spaceBefore=10,
    )
    normal_style = ParagraphStyle("NormStyle", parent=styles["Normal"], fontName=font_name, fontSize=10, leading=14)
    bold_style = ParagraphStyle("BoldStyle", parent=styles["Normal"], fontName=font_name_bold, fontSize=10, leading=14)

    cell_center = ParagraphStyle("CellC", parent=normal_style, alignment=1)
    cell_left = ParagraphStyle("CellL", parent=normal_style, alignment=0)
    cell_right = ParagraphStyle("CellR", parent=normal_style, alignment=2)
    th_center = ParagraphStyle("ThC", parent=bold_style, alignment=1, textColor=colors.white)
    th_left = ParagraphStyle("ThL", parent=bold_style, alignment=0, textColor=colors.white)
    th_right = ParagraphStyle("ThR", parent=bold_style, alignment=2, textColor=colors.white)

    story = [
        Paragraph("<b>АКТ ВИКОНАНИХ РОБІТ</b>", title_style),
        Spacer(1, 5 * mm),
        Paragraph(f"<b>Замовник (клієнт):</b> {_safe(vehicle.get('client'))}", normal_style),
    ]

    if vehicle.get("phone"):
        story.append(Paragraph(f"<b>Телефон:</b> {_safe(vehicle.get('phone'))}", normal_style))

    info_data = [
        [
            Paragraph(f"<b>Дата:</b> {_safe(vehicle.get('date'))}", normal_style),
            Paragraph(f"<b>Держномер:</b> {_safe(vehicle.get('number'))}", normal_style),
        ],
        [
            Paragraph(f"<b>Марка:</b> {_safe(vehicle.get('brand'))}", normal_style),
            Paragraph(f"<b>VIN:</b> {_safe(vehicle.get('vin'))}", normal_style),
        ],
        [
            Paragraph(f"<b>Модель:</b> {_safe(vehicle.get('model'))}", normal_style),
            Paragraph(f"<b>Пробіг:</b> {_safe(vehicle.get('mileage'))} км", normal_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[90 * mm, 90 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    table_styles = (cell_center, cell_left, cell_right, th_center, th_left, th_right)

    story.append(Paragraph("<b>Матеріали</b>", h2_style))
    materials_table, total_materials = _build_items_table(materials, table_styles, col_widths)
    story.append(materials_table)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"<para align='right'><b>Разом матеріали: {total_materials:.2f} грн</b></para>", normal_style))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("<b>Послуги / Роботи</b>", h2_style))
    works_table, total_works = _build_items_table(works, table_styles, col_widths)
    story.append(works_table)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"<para align='right'><b>Разом послуги: {total_works:.2f} грн</b></para>", normal_style))

    story.append(Spacer(1, 7 * mm))
    grand_total_style = ParagraphStyle("Total", parent=normal_style, fontName=font_name_bold, fontSize=13, alignment=2)
    story.append(Paragraph(f"<b>ЗАГАЛЬНА СУМА: {total_materials + total_works:.2f} грн</b>", grand_total_style))

    pdf.build(story)
