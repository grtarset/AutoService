import os
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QDateEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import QDate
from ui.item_dialog import ItemDialog
from reports.pdf_export import export_invoice
import os
import re
from pathlib import Path


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoService — Акти виконаних робіт")
        self.resize(1000, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # =====================================================
        # БЛОК 1: Данi автомобіля
        # =====================================================
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(QDate.currentDate())

        self.brandEdit = QLineEdit()
        self.modelEdit = QLineEdit()
        self.vinEdit = QLineEdit()
        self.numberEdit = QLineEdit()
        self.mileageEdit = QLineEdit()
        self.clientEdit = QLineEdit()
        self.clientEdit.setPlaceholderText("Приклад: Іванов Петро Сидорович")

        form_layout.addRow("Дата:", self.dateEdit)
        form_layout.addRow("ПІБ Клієнта:", self.clientEdit)
        form_layout.addRow("Марка авто:", self.brandEdit)
        form_layout.addRow("Модель авто:", self.modelEdit)
        form_layout.addRow("VIN-код:", self.vinEdit)
        form_layout.addRow("Держномер:", self.numberEdit)
        form_layout.addRow("Пробіг (км):", self.mileageEdit)

        main_layout.addLayout(form_layout)

        # =====================================================
        # БЛОК 2: Таблиця Матеріалів
        # =====================================================
        lbl_materials = QLabel("<b>Використані матеріали та запчастини</b>")
        lbl_materials.setStyleSheet("font-size: 11pt; color: #2b4c7e;")
        main_layout.addWidget(lbl_materials)

        self.materialsTable = QTableWidget(0, 4)
        self.materialsTable.setHorizontalHeaderLabels(["Назва", "Кількість", "Ціна", "Сума"])
        self.materialsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setup_table_headers(self.materialsTable)
        main_layout.addWidget(self.materialsTable)

        btn_mat_layout = QHBoxLayout()
        self.addMaterialButton = QPushButton("➕ Додати матеріал")
        btn_mat_layout.addWidget(self.addMaterialButton)
        btn_mat_layout.addStretch()
        main_layout.addLayout(btn_mat_layout)

        # =====================================================
        # БЛОК 3: Таблиця Послуг / Робіт
        # =====================================================
        lbl_works = QLabel("<b>Виконані послуги та роботи</b>")
        lbl_works.setStyleSheet("font-size: 11pt; color: #2b4c7e;")
        main_layout.addWidget(lbl_works)

        self.worksTable = QTableWidget(0, 4)
        self.worksTable.setHorizontalHeaderLabels(["Назва", "Кількість", "Ціна", "Сума"])
        self.worksTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setup_table_headers(self.worksTable)
        main_layout.addWidget(self.worksTable)

        btn_work_layout = QHBoxLayout()
        self.addWorkButton = QPushButton("➕ Додати послугу")
        btn_work_layout.addWidget(self.addWorkButton)
        btn_work_layout.addStretch()
        main_layout.addLayout(btn_work_layout)

        # =====================================================
        # БЛОК 4: Фінансові підсумки
        # =====================================================
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(5)
        summary_layout.setContentsMargins(0, 10, 0, 10)

        self.materialsTotal = QLabel("Матеріали: 0.00 грн")
        self.worksTotal = QLabel("Послуги: 0.00 грн")
        
        self.totalLabel = QLabel("<b>РАЗОМ ДО ОПЛАТИ: 0.00 грн</b>")
        self.totalLabel.setStyleSheet("font-size: 13pt; color: #1e293b; padding-top: 5px;")

        summary_layout.addWidget(self.materialsTotal)
        summary_layout.addWidget(self.worksTotal)
        summary_layout.addWidget(self.totalLabel)
        main_layout.addLayout(summary_layout)

        # =====================================================
        # БЛОК 5: Головна панель дій
        # =====================================================
        action_buttons = QHBoxLayout()
        self.pdfButton = QPushButton("📄 Сформувати Акт у PDF")
        self.pdfButton.setStyleSheet("font-weight: bold; padding: 6px 15px;")
        
        action_buttons.addStretch()
        action_buttons.addWidget(self.pdfButton)
        main_layout.addLayout(action_buttons)

        # Прив'язка подій до кнопок
        self.addMaterialButton.clicked.connect(self.add_material)
        self.addWorkButton.clicked.connect(self.add_work)
        self.pdfButton.clicked.connect(self.create_pdf)

    def setup_table_headers(self, table: QTableWidget):
        """Налаштування гнучкого розтягування колонок таблиці"""
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)          # Назва займає весь вільний простір
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Кількість підганяється під текст
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Ціна підганяється під текст
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # Сума теж гарно розтягується

    def get_short_fio(self, full_name: str) -> str:
        """Перетворює 'Іванов Петро Сидорович' на 'Іванов П.С.' або повертає оригінал, якщо формат інший"""
        parts = full_name.strip().split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
        elif len(parts) == 2:
            return f"{parts[0]} {parts[1][0]}."
        elif len(parts) == 1 and parts[0]:
            return parts[0]
        return "Клієнт"

    def clean_filename(self, filename: str) -> str:
        """Видаляє символи, які заборонені в назвах файлів Windows (:, /, \, *, ?, ", <, >, |)"""
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def calculate_totals(self):
        """Обчислення проміжних підсумків та фінальної суми акту"""
        materials_sum = 0.0
        for row in range(self.materialsTable.rowCount()):
            try:
                materials_sum += float(self.materialsTable.item(row, 3).text())
            except (ValueError, AttributeError):
                continue

        works_sum = 0.0
        for row in range(self.worksTable.rowCount()):
            try:
                works_sum += float(self.worksTable.item(row, 3).text())
            except (ValueError, AttributeError):
                continue

        self.materialsTotal.setText(f"Матеріали: <b>{materials_sum:.2f}</b> грн")
        self.worksTotal.setText(f"Послуги: <b>{works_sum:.2f}</b> грн")
        self.totalLabel.setText(f"<b>РАЗОМ ДО ОПЛАТИ: <font color='#2b4c7e'>{materials_sum + works_sum:.2f}</font> грн</b>")

    def create_pdf(self):
        # 1. Збір даних автомобіля
        vehicle = {
            "date": self.dateEdit.date().toString("dd.MM.yyyy"),
            "brand": self.brandEdit.text().strip(),
            "model": self.modelEdit.text().strip(),
            "vin": self.vinEdit.text().strip(),
            "number": self.numberEdit.text().strip(),
            "mileage": self.mileageEdit.text().strip(),
            "client": self.clientEdit.text().strip()
        }

        # 2. Формування динамічного шляху: Робочий стіл -> папка "Акти"
        desktop_path = Path(os.path.expanduser("~")) / "Desktop"
        target_dir = desktop_path / "Акти"
        
        # Автоматично створюємо папку "Акти", якщо її ще немає
        target_dir.mkdir(parents=True, exist_ok=True)

        # 3. Генерація назви файлу за вашим правилом: ПІБ скорочено, авто, дата
        short_fio = self.get_short_fio(vehicle["client"])
        car_info = f"{vehicle['brand']} {vehicle['model']}".strip()
        if not car_info:
            car_info = "Авто"
            
        raw_filename = f"{short_fio}, {car_info}, {vehicle['date']}.pdf"
        # Очищаємо назву від заборонених у Windows символів
        safe_filename = self.clean_filename(raw_filename)
        
        # Повний шлях до фінального файлу
        full_pdf_path = str(target_dir / safe_filename)

        # 4. Збір таблиці матеріалів
        materials = []
        for row in range(self.materialsTable.rowCount()):
            qty = float(self.materialsTable.item(row, 1).text())
            price = float(self.materialsTable.item(row, 2).text())
            materials.append({
                "name": self.materialsTable.item(row, 0).text(),
                "qty": qty,
                "price": price,
                "sum": qty * price
            })

        # 5. Збір таблиці послуг
        works = []
        for row in range(self.worksTable.rowCount()):
            qty = float(self.worksTable.item(row, 1).text())
            price = float(self.worksTable.item(row, 2).text())
            works.append({
                "name": self.worksTable.item(row, 0).text(),
                "qty": qty,
                "price": price,
                "sum": qty * price
            })

        # Передаємо сформований повний шлях у вашу функцію експорту ReportLab
        export_invoice(full_pdf_path, vehicle, materials, works)
        
        print(f"Збережено в: {full_pdf_path}")

    def add_material(self):
        dialog = ItemDialog("Матеріал")
        if dialog.exec():
            name, qty, price = dialog.get_data()
            row = self.materialsTable.rowCount()
            self.materialsTable.insertRow(row)

            self.materialsTable.setItem(row, 0, QTableWidgetItem(name))
            self.materialsTable.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.materialsTable.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
            self.materialsTable.setItem(row, 3, QTableWidgetItem(f"{qty * price:.2f}"))

            self.calculate_totals()

    def add_work(self):
        dialog = ItemDialog("Послуга")
        if dialog.exec():
            name, qty, price = dialog.get_data()
            row = self.worksTable.rowCount()
            self.worksTable.insertRow(row)

            self.worksTable.setItem(row, 0, QTableWidgetItem(name))
            self.worksTable.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.worksTable.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
            self.worksTable.setItem(row, 3, QTableWidgetItem(f"{qty * price:.2f}"))

            self.calculate_totals()