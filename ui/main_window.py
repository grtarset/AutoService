import os
import re
from pathlib import Path
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
    QAbstractItemView,
    QMessageBox
)
from PySide6.QtCore import QDate
from ui.item_dialog import ItemDialog
from reports.pdf_export import export_invoice
from database.db_manager import save_invoice, get_invoice_by_id
from ui.history_dialog import HistoryDialog


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.current_invoice_id = None  # None означає новий акт. Якщо тут число — ми його редагуємо.

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
        self.materialsTable.setSelectionBehavior(QAbstractItemView.SelectRows) # <-- ВИПРАВЛЕНО: Перенесено сюди
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
        self.worksTable.setSelectionBehavior(QAbstractItemView.SelectRows) # <-- ВИПРАВЛЕНО: Перенесено сюди
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
        self.btn_new = QPushButton("🆕 Нова накладна")
        self.btn_history = QPushButton("🗂️ Журнал актів")
        self.btn_save = QPushButton("💾 Зберегти в БД")
        self.pdfButton = QPushButton("📄 Сформувати Акт у PDF")

        self.pdfButton.setStyleSheet("font-weight: bold; padding: 6px 15px;")

        action_buttons.addWidget(self.btn_new)
        action_buttons.addWidget(self.btn_history)
        action_buttons.addStretch()
        action_buttons.addWidget(self.btn_save)
        action_buttons.addWidget(self.pdfButton)
        main_layout.addLayout(action_buttons)

        # =====================================================
        # ПРИВ'ЯЗКА ПОДІЙ
        # =====================================================
        self.addMaterialButton.clicked.connect(self.add_material)
        self.addWorkButton.clicked.connect(self.add_work)
        
        self.btn_new.clicked.connect(self.clear_form_to_new)
        self.btn_save.clicked.connect(self.save_to_db)
        self.btn_history.clicked.connect(self.open_history)
        self.pdfButton.clicked.connect(self.create_pdf)

        # Перехоплення натискання клавіш для видалення (Del)
        self.materialsTable.keyPressEvent = lambda event: self.table_key_press(event, self.materialsTable)
        self.worksTable.keyPressEvent = lambda event: self.table_key_press(event, self.worksTable)

    def collect_form_data(self):
        """Збирає дані з інтерфейсу в структуровані словники/списки"""
        vehicle = {
            "date": self.dateEdit.date().toString("dd.MM.yyyy"),
            "brand": self.brandEdit.text().strip(),
            "model": self.modelEdit.text().strip(),
            "vin": self.vinEdit.text().strip(),
            "number": self.numberEdit.text().strip(),
            "mileage": self.mileageEdit.text().strip(),
            "client": self.clientEdit.text().strip()
        }

        materials = []
        for row in range(self.materialsTable.rowCount()):
            materials.append({
                "name": self.materialsTable.item(row, 0).text(),
                "qty": float(self.materialsTable.item(row, 1).text()),
                "price": float(self.materialsTable.item(row, 2).text())
            })

        works = []
        for row in range(self.worksTable.rowCount()):
            works.append({
                "name": self.worksTable.item(row, 0).text(),
                "qty": float(self.worksTable.item(row, 1).text()),
                "price": float(self.worksTable.item(row, 2).text())
            })
            
        return vehicle, materials, works

    def clear_form_to_new(self):
        """Очищає форму та скидає стан програми для створення нової накладної"""
        self.current_invoice_id = None
        self.setWindowTitle("AutoService — Акти виконаних робіт")
        
        self.clientEdit.clear()
        self.brandEdit.clear()
        self.modelEdit.clear()
        self.vinEdit.clear()
        self.numberEdit.clear()
        self.mileageEdit.clear()
        
        self.dateEdit.setDate(QDate.currentDate())
        self.materialsTable.setRowCount(0)
        self.worksTable.setRowCount(0)
        
        self.calculate_totals()

    def save_to_db(self):
        """Зберігає поточний стан форми в базу даних SQLite"""
        try:
            vehicle, materials, works = self.collect_form_data()
            invoice_id = save_invoice(vehicle, materials, works, self.current_invoice_id)
            
            self.current_invoice_id = invoice_id
            self.setWindowTitle(f"AutoService — РЕДАГУВАННЯ НАКЛАДНОЇ №{invoice_id}")
            return invoice_id
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти накладну: {str(e)}")
            return None

    def open_history(self):
        """Відкриває журнал і завантажує обрану накладну для редагування"""
        dialog = HistoryDialog(self)
        if dialog.exec():
            invoice_id = dialog.get_selected_id()
            if invoice_id:
                self.load_invoice_for_editing(invoice_id)

    def load_invoice_for_editing(self, invoice_id):
        """Заповнює форму даними з бази даних"""
        vehicle, materials, works = get_invoice_by_id(invoice_id)
        
        self.current_invoice_id = invoice_id
        
        self.dateEdit.setDate(QDate.fromString(vehicle['date'], "dd.MM.yyyy"))
        self.clientEdit.setText(vehicle['client'])
        self.brandEdit.setText(vehicle['brand'])
        self.modelEdit.setText(vehicle['model'])
        self.vinEdit.setText(vehicle['vin'])
        self.numberEdit.setText(vehicle['number'])
        self.mileageEdit.setText(vehicle['mileage'])
        
        self.materialsTable.setRowCount(0)
        for row, m in enumerate(materials):
            self.materialsTable.insertRow(row)
            self.materialsTable.setItem(row, 0, QTableWidgetItem(m['name']))
            self.materialsTable.setItem(row, 1, QTableWidgetItem(str(m['qty'])))
            self.materialsTable.setItem(row, 2, QTableWidgetItem(f"{m['price']:.2f}"))
            self.materialsTable.setItem(row, 3, QTableWidgetItem(f"{m['sum']:.2f}"))
            
        self.worksTable.setRowCount(0)
        for row, w in enumerate(works):
            self.worksTable.insertRow(row)
            self.worksTable.setItem(row, 0, QTableWidgetItem(w['name']))
            self.worksTable.setItem(row, 1, QTableWidgetItem(str(w['qty'])))
            self.worksTable.setItem(row, 2, QTableWidgetItem(f"{w['price']:.2f}"))
            self.worksTable.setItem(row, 3, QTableWidgetItem(f"{w['sum']:.2f}"))
            
        self.calculate_totals()
        self.setWindowTitle(f"AutoService — РЕДАГУВАННЯ НАКЛАДНОЇ №{invoice_id}")

    def setup_table_headers(self, table: QTableWidget):
        """Налаштування гнучкого розтягування колонок таблиці"""
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

    def get_short_fio(self, full_name: str) -> str:
        """Перетворює 'Іванов Петро Сидорович' на 'Іванов П.С.'"""
        parts = full_name.strip().split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
        elif len(parts) == 2:
            return f"{parts[0]} {parts[1][0]}."
        elif len(parts) == 1 and parts[0]:
            return parts[0]
        return "Клієнт"

    def clean_filename(self, filename: str) -> str:
        """Видаляє символи, які заборонені в назвах файлів Windows"""
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
        # 1. АВТОЗБЕРЕЖЕННЯ В БД ПЕРЕД СТВОРЕННЯМ PDF
        invoice_id = self.save_to_db()
        if not invoice_id:
            return # Зупиняємо процес, якщо під час збереження сталася помилка

        # 2. Збір актуальних даних для формування документу
        vehicle, materials, works = self.collect_form_data()

        # 3. Визначення Робочого столу з урахуванням хмари OneDrive та мови ОС
        home_path = Path(os.path.expanduser("~"))
        onedrive_desktop = home_path / "OneDrive" / "Desktop"
        onedrive_desktop_ua = home_path / "OneDrive" / "Робочий стіл"
        standard_desktop = home_path / "Desktop"
        standard_desktop_ua = home_path / "Робочий стіл"
        
        if onedrive_desktop.exists():
            desktop_path = onedrive_desktop
        elif onedrive_desktop_ua.exists():
            desktop_path = onedrive_desktop_ua
        elif standard_desktop_ua.exists():
            desktop_path = standard_desktop_ua
        else:
            desktop_path = standard_desktop

        target_dir = desktop_path / "Акти"
        target_dir.mkdir(parents=True, exist_ok=True)

        # 4. Генерація назви файлу за правилом
        short_fio = self.get_short_fio(vehicle["client"])
        car_info = f"{vehicle['brand']} {vehicle['model']}".strip()
        if not car_info:
            car_info = "Авто"
            
        raw_filename = f"{short_fio}, {car_info}, {vehicle['date']}.pdf"
        safe_filename = self.clean_filename(raw_filename)
        full_pdf_path = str(target_dir / safe_filename)

        # 5. Обчислюємо фінальні суми елементів для передачі в PDF
        for m in materials:
            m['sum'] = m['qty'] * m['price']
        for w in works:
            w['sum'] = w['qty'] * w['price']

        # 6. Експорт та автоматичне відкриття провідника
        try:
            export_invoice(full_pdf_path, vehicle, materials, works)
            os.startfile(str(target_dir))
            QMessageBox.information(self, "Успіх", f"Акт успішно збережено в БД (№{invoice_id}) та експортовано в PDF:\n{safe_filename}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка PDF", f"Не вдалося згенерувати PDF-файл: {str(e)}")
            
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

    def table_key_press(self, event, table: QTableWidget):
        """Видаляє виділений рядок при натисканні клавіші Delete"""
        from PySide6.QtCore import Qt
        if event.key() == Qt.Key_Delete:
            selected_rows = sorted(set(index.row() for index in table.selectedIndexes()), reverse=True)
            if selected_rows:
                for row in selected_rows:
                    table.removeRow(row)
                self.calculate_totals() # Перераховуємо суму після видалення
        else:
            QTableWidget.keyPressEvent(table, event)