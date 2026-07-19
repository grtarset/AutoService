import os
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def export_invoice(filename, vehicle, materials, works):
    # 1. Реєстрація українських шрифтів (звичайний та жирний Arial із Windows)
    fonts_dir = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts')
    font_path = os.path.join(fonts_dir, 'arial.ttf')
    bold_font_path = os.path.join(fonts_dir, 'arialbd.ttf')
    
    if os.path.exists(font_path) and os.path.exists(bold_font_path):
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        pdfmetrics.registerFont(TTFont('Arial-Bold', bold_font_path))
        font_name = 'Arial'
        font_name_bold = 'Arial-Bold'
    else:
        font_name = 'Helvetica' 
        font_name_bold = 'Helvetica-Bold'

    # Налаштування стилів сторінки
    pdf = SimpleDocTemplate(
        filename,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    # Розрахунок ширини таблиці (180мм корисної ширини)
    col_widths = [10 * mm, 95 * mm, 20 * mm, 25 * mm, 30 * mm]
    
    styles = getSampleStyleSheet()
    
    # Створюємо власні стилі з підтримкою нашого шрифту (ПОМИЛКУ ВИПРАВЛЕНО ТУТ)
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=font_name_bold, fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#2b4c7e"))
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontName=font_name_bold, fontSize=12, leading=16, textColor=colors.HexColor("#2b4c7e"), spaceBefore=10)
    normal_style = ParagraphStyle('NormStyle', parent=styles['Normal'], fontName=font_name, fontSize=10, leading=14)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName=font_name_bold, fontSize=10, leading=14) 
    
    # Стилі для тексту всередині таблиць
    cell_center = ParagraphStyle('CellC', parent=normal_style, alignment=1)
    cell_left = ParagraphStyle('CellL', parent=normal_style, alignment=0)
    cell_right = ParagraphStyle('CellR', parent=normal_style, alignment=2)
    
    th_center = ParagraphStyle('ThC', parent=bold_style, alignment=1, textColor=colors.white)
    th_left = ParagraphStyle('ThL', parent=bold_style, alignment=0, textColor=colors.white)
    th_right = ParagraphStyle('ThR', parent=bold_style, alignment=2, textColor=colors.white)

    story = []

    # Заголовок
    story.append(Paragraph("<b>АКТ ВИКОНАНИХ РОБІТ</b>", title_style))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph(f"<b>Замовник (Клієнт):</b> {vehicle['client']}", normal_style))
    # Інформація про авто (робимо таблицею у два стовпчики, щоб було гарно)
    info_data = [
        [Paragraph(f"<b>Дата:</b> {vehicle['date']}", normal_style), Paragraph(f"<b>Держномер:</b> {vehicle['number']}", normal_style)],
        [Paragraph(f"<b>Марка:</b> {vehicle['brand']}", normal_style), Paragraph(f"<b>VIN:</b> {vehicle['vin']}", normal_style)],
        [Paragraph(f"<b>Модель:</b> {vehicle['model']}", normal_style), Paragraph(f"<b>Пробіг:</b> {vehicle['mileage']} км", normal_style)]
    ]
    info_table = Table(info_data, colWidths=[90*mm, 90*mm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    # --- МАТЕРІАЛИ ---
    story.append(Paragraph("<b>Матеріали</b>", h2_style))
    
    table_data = [[
        Paragraph("<b>№</b>", th_center),
        Paragraph("<b>Назва</b>", th_left),
        Paragraph("<b>К-сть</b>", th_center),
        Paragraph("<b>Ціна</b>", th_right),
        Paragraph("<b>Сума</b>", th_right)
    ]]

    total_materials = 0
    for i, item in enumerate(materials, start=1):
        table_data.append([
            Paragraph(str(i), cell_center),
            Paragraph(item["name"], cell_left),
            Paragraph(str(item["qty"]), cell_center),
            Paragraph(f"{item['price']:.2f}", cell_right),
            Paragraph(f"{item['sum']:.2f}", cell_right)
        ])
        total_materials += item["sum"]

    t_materials = Table(table_data, colWidths=col_widths)
    t_materials.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2b4c7e")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t_materials)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"<para align='right'><b>Разом матеріали: {total_materials:.2f} грн</b></para>", normal_style))
    story.append(Spacer(1, 5 * mm))

    # --- ПОСЛУГИ ---
    story.append(Paragraph("<b>Послуги / Роботи</b>", h2_style))
    
    table_data = [[
        Paragraph("<b>№</b>", th_center),
        Paragraph("<b>Назва</b>", th_left),
        Paragraph("<b>К-сть</b>", th_center),
        Paragraph("<b>Ціна</b>", th_right),
        Paragraph("<b>Сума</b>", th_right)
    ]]

    total_works = 0
    for i, item in enumerate(works, start=1):
        table_data.append([
            Paragraph(str(i), cell_center),
            Paragraph(item["name"], cell_left),
            Paragraph(str(item["qty"]), cell_center),
            Paragraph(f"{item['price']:.2f}", cell_right),
            Paragraph(f"{item['sum']:.2f}", cell_right)
        ])
        total_works += item["sum"]

    t_works = Table(table_data, colWidths=col_widths)
    t_works.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2b4c7e")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t_works)
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"<para align='right'><b>Разом послуги: {total_works:.2f} грн</b></para>", normal_style))
    
    # --- ЗАГАЛЬНА СУМА ---
    story.append(Spacer(1, 7 * mm))
    grand_total_style = ParagraphStyle('Total', parent=normal_style, fontName=font_name, fontSize=13, alignment=2)
    story.append(Paragraph(f"<b>ЗАГАЛЬНА СУМА: {total_materials + total_works:.2f} грн</b>", grand_total_style))

    pdf.build(story)