from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

styles = getSampleStyleSheet()


def export_invoice(filename, vehicle, materials, works):

    pdf = SimpleDocTemplate(filename)

    story = []

    story.append(Paragraph("<b>АКТ ВИКОНАНИХ РОБІТ</b>", styles["Heading1"]))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph(f"Дата: {vehicle['date']}", styles["Normal"]))
    story.append(Paragraph(f"Марка: {vehicle['brand']}", styles["Normal"]))
    story.append(Paragraph(f"Модель: {vehicle['model']}", styles["Normal"]))
    story.append(Paragraph(f"VIN: {vehicle['vin']}", styles["Normal"]))
    story.append(Paragraph(f"Держномер: {vehicle['number']}", styles["Normal"]))
    story.append(Paragraph(f"Пробіг: {vehicle['mileage']}", styles["Normal"]))

    story.append(Spacer(1, 8 * mm))

    ##################################################
    # Матеріали
    ##################################################

    story.append(Paragraph("<b>Матеріали</b>", styles["Heading2"]))

    table_data = [
        ["№", "Назва", "К-сть", "Ціна", "Сума"]
    ]

    total_materials = 0

    for i, item in enumerate(materials, start=1):

        table_data.append([
            i,
            item["name"],
            item["qty"],
            f"{item['price']:.2f}",
            f"{item['sum']:.2f}"
        ])

        total_materials += item["sum"]

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))

    story.append(table)

    story.append(
        Paragraph(
            f"<b>Разом матеріали: {total_materials:.2f} грн</b>",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 8 * mm))

    ##################################################
    # Роботи
    ##################################################

    story.append(Paragraph("<b>Послуги</b>", styles["Heading2"]))

    table_data = [
        ["№", "Назва", "К-сть", "Ціна", "Сума"]
    ]

    total_works = 0

    for i, item in enumerate(works, start=1):

        table_data.append([
            i,
            item["name"],
            item["qty"],
            f"{item['price']:.2f}",
            f"{item['sum']:.2f}"
        ])

        total_works += item["sum"]

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
    ]))

    story.append(table)

    story.append(
        Paragraph(
            f"<b>Разом послуги: {total_works:.2f} грн</b>",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 10 * mm))

    story.append(
        Paragraph(
            f"<b>ЗАГАЛЬНА СУМА: {total_materials + total_works:.2f} грн</b>",
            styles["Heading2"]
        )
    )

    pdf.build(story)