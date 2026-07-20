import os
import re
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import app_icon
from database.db_manager import get_invoice_by_id, save_invoice, search_customer_records
from reports.pdf_export import export_invoice
from ui.clients_dialog import ClientsDialog
from ui.history_dialog import HistoryDialog
from ui.item_dialog import ItemDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_invoice_id = None
        self.current_client_id = None
        self.current_vehicle_id = None
        self._loading_customer = False

        self.setWindowTitle("AutoService — Акти виконаних робіт")
        self.setWindowIcon(app_icon())
        self.resize(1080, 790)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        lookup_title = QLabel("<b>Пошук клієнта або автомобіля</b>")
        lookup_title.setStyleSheet("font-size: 11pt; color: #2b4c7e;")
        main_layout.addWidget(lookup_title)

        lookup_layout = QHBoxLayout()
        self.lookupEdit = QLineEdit()
        self.lookupEdit.setPlaceholderText("ПІБ, телефон, VIN або держномер")
        self.lookupButton = QPushButton("Знайти")
        lookup_layout.addWidget(self.lookupEdit, 2)
        lookup_layout.addWidget(self.lookupButton)
        main_layout.addLayout(lookup_layout)

        lookup_result_layout = QHBoxLayout()
        self.lookupCombo = QComboBox()
        self.lookupCombo.setMinimumWidth(520)
        self.applyLookupButton = QPushButton("Обрати")
        self.clearCustomerButton = QPushButton("Очистити вибір")
        lookup_result_layout.addWidget(self.lookupCombo, 1)
        lookup_result_layout.addWidget(self.applyLookupButton)
        lookup_result_layout.addWidget(self.clearCustomerButton)
        main_layout.addLayout(lookup_result_layout)

        self.selectedCustomerLabel = QLabel("Новий клієнт / автомобіль")
        self.selectedCustomerLabel.setStyleSheet("color: #64748b;")
        main_layout.addWidget(self.selectedCustomerLabel)

        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(QDate.currentDate())

        self.clientEdit = QLineEdit()
        self.clientEdit.setPlaceholderText("Приклад: Іванов Петро Сидорович")
        self.phoneEdit = QLineEdit()
        self.phoneEdit.setPlaceholderText("+380...")
        self.brandEdit = QLineEdit()
        self.modelEdit = QLineEdit()
        self.vinEdit = QLineEdit()
        self.numberEdit = QLineEdit()
        self.mileageEdit = QLineEdit()

        form_layout.addRow("Дата:", self.dateEdit)
        form_layout.addRow("ПІБ клієнта:", self.clientEdit)
        form_layout.addRow("Телефон:", self.phoneEdit)
        form_layout.addRow("Марка авто:", self.brandEdit)
        form_layout.addRow("Модель авто:", self.modelEdit)
        form_layout.addRow("VIN-код:", self.vinEdit)
        form_layout.addRow("Держномер:", self.numberEdit)
        form_layout.addRow("Пробіг (км):", self.mileageEdit)
        main_layout.addLayout(form_layout)

        lbl_materials = QLabel("<b>Використані матеріали та запчастини</b>")
        lbl_materials.setStyleSheet("font-size: 11pt; color: #2b4c7e;")
        main_layout.addWidget(lbl_materials)

        self.materialsTable = QTableWidget(0, 4)
        self.materialsTable.setHorizontalHeaderLabels(["Назва", "Кількість", "Ціна", "Сума"])
        self.materialsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.materialsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setup_table_headers(self.materialsTable)
        main_layout.addWidget(self.materialsTable)

        btn_mat_layout = QHBoxLayout()
        self.addMaterialButton = QPushButton("➕ Додати матеріал")
        btn_mat_layout.addWidget(self.addMaterialButton)
        btn_mat_layout.addStretch()
        main_layout.addLayout(btn_mat_layout)

        lbl_works = QLabel("<b>Виконані послуги та роботи</b>")
        lbl_works.setStyleSheet("font-size: 11pt; color: #2b4c7e;")
        main_layout.addWidget(lbl_works)

        self.worksTable = QTableWidget(0, 4)
        self.worksTable.setHorizontalHeaderLabels(["Назва", "Кількість", "Ціна", "Сума"])
        self.worksTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.worksTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setup_table_headers(self.worksTable)
        main_layout.addWidget(self.worksTable)

        btn_work_layout = QHBoxLayout()
        self.addWorkButton = QPushButton("➕ Додати послугу")
        btn_work_layout.addWidget(self.addWorkButton)
        btn_work_layout.addStretch()
        main_layout.addLayout(btn_work_layout)

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

        action_buttons = QHBoxLayout()
        self.btn_new = QPushButton("🆕 Новий акт")
        self.btn_clients = QPushButton("👥 Журнал клієнтів")
        self.btn_history = QPushButton("🗂️ Журнал актів")
        self.btn_save = QPushButton("💾 Зберегти")
        self.pdfButton = QPushButton("📄 Сформувати акт у PDF")
        self.pdfButton.setStyleSheet("font-weight: bold; padding: 6px 15px;")

        action_buttons.addWidget(self.btn_new)
        action_buttons.addWidget(self.btn_clients)
        action_buttons.addWidget(self.btn_history)
        action_buttons.addStretch()
        action_buttons.addWidget(self.btn_save)
        action_buttons.addWidget(self.pdfButton)
        main_layout.addLayout(action_buttons)

        self.lookupButton.clicked.connect(self.refresh_customer_lookup)
        self.lookupEdit.returnPressed.connect(self.refresh_customer_lookup)
        self.lookupEdit.textChanged.connect(self.refresh_customer_lookup)
        self.applyLookupButton.clicked.connect(self.apply_selected_customer)
        self.clearCustomerButton.clicked.connect(self.clear_customer_selection)

        self.clientEdit.textEdited.connect(self.reset_customer_ids_after_manual_edit)
        self.phoneEdit.textEdited.connect(self.reset_customer_ids_after_manual_edit)
        self.brandEdit.textEdited.connect(self.reset_customer_ids_after_manual_edit)
        self.modelEdit.textEdited.connect(self.reset_customer_ids_after_manual_edit)
        self.vinEdit.textEdited.connect(self.reset_customer_ids_after_manual_edit)
        self.numberEdit.textEdited.connect(self.reset_customer_ids_after_manual_edit)

        self.addMaterialButton.clicked.connect(self.add_material)
        self.addWorkButton.clicked.connect(self.add_work)
        self.btn_new.clicked.connect(self.clear_form_to_new)
        self.btn_clients.clicked.connect(self.open_clients)
        self.btn_save.clicked.connect(self.save_to_db)
        self.btn_history.clicked.connect(self.open_history)
        self.pdfButton.clicked.connect(self.create_pdf)

        self.materialsTable.keyPressEvent = lambda event: self.table_key_press(event, self.materialsTable)
        self.worksTable.keyPressEvent = lambda event: self.table_key_press(event, self.worksTable)

        self.refresh_customer_lookup()

    def refresh_customer_lookup(self, _text=None):
        query = self.lookupEdit.text().strip()
        records = search_customer_records(query)

        self.lookupCombo.blockSignals(True)
        self.lookupCombo.clear()
        if records:
            for record in records:
                self.lookupCombo.addItem(record["label"], record)
        else:
            self.lookupCombo.addItem("Нічого не знайдено", None)
        self.lookupCombo.blockSignals(False)

        has_records = bool(records)
        self.lookupCombo.setEnabled(has_records)
        self.applyLookupButton.setEnabled(has_records)

    def apply_selected_customer(self):
        record = self.lookupCombo.currentData()
        if not record:
            return

        self.apply_customer_record(record)

    def apply_customer_record(self, record):
        self._loading_customer = True
        self.current_client_id = record.get("client_id")
        self.current_vehicle_id = record.get("vehicle_id")

        self.clientEdit.setText(record.get("client") or "")
        self.phoneEdit.setText(record.get("phone") or "")
        self.brandEdit.setText(record.get("brand") or "")
        self.modelEdit.setText(record.get("model") or "")
        self.vinEdit.setText(record.get("vin") or "")
        self.numberEdit.setText(record.get("number") or "")
        self.mileageEdit.setText(record.get("mileage") or "")
        self._loading_customer = False

        self.update_customer_label()

    def clear_customer_selection(self):
        self.current_client_id = None
        self.current_vehicle_id = None
        self.update_customer_label()

    def reset_customer_ids_after_manual_edit(self):
        if self._loading_customer:
            return
        self.current_client_id = None
        self.current_vehicle_id = None
        self.update_customer_label()

    def update_customer_label(self):
        if self.current_client_id or self.current_vehicle_id:
            client = self.clientEdit.text().strip() or "Клієнт"
            car = f"{self.brandEdit.text().strip()} {self.modelEdit.text().strip()}".strip()
            number = self.numberEdit.text().strip()
            suffix = " / ".join(part for part in (car, number) if part)
            if suffix:
                self.selectedCustomerLabel.setText(f"Обрано: {client} — {suffix}")
            else:
                self.selectedCustomerLabel.setText(f"Обрано: {client}")
        else:
            self.selectedCustomerLabel.setText("Новий клієнт / автомобіль")

    def collect_form_data(self):
        vehicle = {
            "date": self.dateEdit.date().toString("dd.MM.yyyy"),
            "client": self.clientEdit.text().strip(),
            "phone": self.phoneEdit.text().strip(),
            "brand": self.brandEdit.text().strip(),
            "model": self.modelEdit.text().strip(),
            "vin": self.vinEdit.text().strip(),
            "number": self.numberEdit.text().strip(),
            "mileage": self.mileageEdit.text().strip(),
            "client_id": self.current_client_id,
            "vehicle_id": self.current_vehicle_id,
        }

        materials = []
        for row in range(self.materialsTable.rowCount()):
            materials.append({
                "name": self.materialsTable.item(row, 0).text(),
                "qty": float(self.materialsTable.item(row, 1).text()),
                "price": float(self.materialsTable.item(row, 2).text()),
            })

        works = []
        for row in range(self.worksTable.rowCount()):
            works.append({
                "name": self.worksTable.item(row, 0).text(),
                "qty": float(self.worksTable.item(row, 1).text()),
                "price": float(self.worksTable.item(row, 2).text()),
            })

        return vehicle, materials, works

    def clear_form_to_new(self):
        self.current_invoice_id = None
        self.current_client_id = None
        self.current_vehicle_id = None
        self.setWindowTitle("AutoService — Акти виконаних робіт")

        self.clientEdit.clear()
        self.phoneEdit.clear()
        self.brandEdit.clear()
        self.modelEdit.clear()
        self.vinEdit.clear()
        self.numberEdit.clear()
        self.mileageEdit.clear()

        self.dateEdit.setDate(QDate.currentDate())
        self.materialsTable.setRowCount(0)
        self.worksTable.setRowCount(0)

        self.calculate_totals()
        self.update_customer_label()

    def save_to_db(self):
        try:
            vehicle, materials, works = self.collect_form_data()
            invoice_id = save_invoice(vehicle, materials, works, self.current_invoice_id)

            saved_vehicle, _, _ = get_invoice_by_id(invoice_id)
            self.current_invoice_id = invoice_id
            self.current_client_id = saved_vehicle.get("client_id")
            self.current_vehicle_id = saved_vehicle.get("vehicle_id")
            self.setWindowTitle(f"AutoService — РЕДАГУВАННЯ АКТУ №{invoice_id}")
            self.update_customer_label()
            self.refresh_customer_lookup()
            return invoice_id
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти акт: {str(e)}")
            return None

    def open_history(self):
        dialog = HistoryDialog(self)
        if dialog.exec():
            invoice_id = dialog.get_selected_id()
            if invoice_id:
                self.load_invoice_for_editing(invoice_id)

    def open_clients(self):
        dialog = ClientsDialog(self)
        if dialog.exec():
            record = dialog.get_selected_record()
            if record:
                self.apply_customer_record(record)
                self.refresh_customer_lookup()

    def load_invoice_for_editing(self, invoice_id):
        vehicle, materials, works = get_invoice_by_id(invoice_id)

        self._loading_customer = True
        self.current_invoice_id = invoice_id
        self.current_client_id = vehicle.get("client_id")
        self.current_vehicle_id = vehicle.get("vehicle_id")

        date = QDate.fromString(vehicle["date"], "dd.MM.yyyy")
        self.dateEdit.setDate(date if date.isValid() else QDate.currentDate())
        self.clientEdit.setText(vehicle.get("client") or "")
        self.phoneEdit.setText(vehicle.get("phone") or "")
        self.brandEdit.setText(vehicle.get("brand") or "")
        self.modelEdit.setText(vehicle.get("model") or "")
        self.vinEdit.setText(vehicle.get("vin") or "")
        self.numberEdit.setText(vehicle.get("number") or "")
        self.mileageEdit.setText(vehicle.get("mileage") or "")
        self._loading_customer = False

        self.materialsTable.setRowCount(0)
        for row, item in enumerate(materials):
            self.materialsTable.insertRow(row)
            self.materialsTable.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.materialsTable.setItem(row, 1, QTableWidgetItem(str(item["qty"])))
            self.materialsTable.setItem(row, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            self.materialsTable.setItem(row, 3, QTableWidgetItem(f"{item['sum']:.2f}"))

        self.worksTable.setRowCount(0)
        for row, item in enumerate(works):
            self.worksTable.insertRow(row)
            self.worksTable.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.worksTable.setItem(row, 1, QTableWidgetItem(str(item["qty"])))
            self.worksTable.setItem(row, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            self.worksTable.setItem(row, 3, QTableWidgetItem(f"{item['sum']:.2f}"))

        self.calculate_totals()
        self.update_customer_label()
        self.setWindowTitle(f"AutoService — РЕДАГУВАННЯ АКТУ №{invoice_id}")

    def setup_table_headers(self, table: QTableWidget):
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

    def get_short_fio(self, full_name: str) -> str:
        parts = full_name.strip().split()
        if len(parts) >= 3:
            return f"{parts[0]} {parts[1][0]}.{parts[2][0]}."
        if len(parts) == 2:
            return f"{parts[0]} {parts[1][0]}."
        if len(parts) == 1 and parts[0]:
            return parts[0]
        return "Клієнт"

    def clean_filename(self, filename: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def calculate_totals(self):
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
        self.totalLabel.setText(
            f"<b>РАЗОМ ДО ОПЛАТИ: <font color='#2b4c7e'>{materials_sum + works_sum:.2f}</font> грн</b>"
        )

    def create_pdf(self):
        invoice_id = self.save_to_db()
        if not invoice_id:
            return

        vehicle, materials, works = self.collect_form_data()

        home_path = Path(os.path.expanduser("~"))
        desktop_candidates = [
            home_path / "OneDrive" / "Desktop",
            home_path / "OneDrive" / "Робочий стіл",
            home_path / "Desktop",
            home_path / "Робочий стіл",
        ]
        desktop_path = next((path for path in desktop_candidates if path.exists()), desktop_candidates[2])

        target_dir = desktop_path / "Акти"
        target_dir.mkdir(parents=True, exist_ok=True)

        short_fio = self.get_short_fio(vehicle["client"])
        car_info = f"{vehicle['brand']} {vehicle['model']}".strip() or "Авто"
        raw_filename = f"{short_fio}, {car_info}, {vehicle['date']}.pdf"
        safe_filename = self.clean_filename(raw_filename)
        full_pdf_path = str(target_dir / safe_filename)

        for item in materials:
            item["sum"] = item["qty"] * item["price"]
        for item in works:
            item["sum"] = item["qty"] * item["price"]

        try:
            export_invoice(full_pdf_path, vehicle, materials, works)
            os.startfile(str(target_dir))
            QMessageBox.information(
                self,
                "Успіх",
                f"Акт успішно збережено в БД (№{invoice_id}) та експортовано в PDF:\n{safe_filename}",
            )
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
        if event.key() == Qt.Key_Delete:
            selected_rows = sorted(set(index.row() for index in table.selectedIndexes()), reverse=True)
            if selected_rows:
                for row in selected_rows:
                    table.removeRow(row)
                self.calculate_totals()
        else:
            QTableWidget.keyPressEvent(table, event)
