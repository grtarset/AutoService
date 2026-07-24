import os
import re
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import app_icon, resource_path
from database.db_manager import get_invoice_by_id, save_invoice, search_customer_records
from models.discounts import (
    DISCOUNT_AMOUNT,
    DISCOUNT_NONE,
    DISCOUNT_PERCENT,
    calculate_invoice_totals,
    format_discount,
    normalize_discount_type,
    prepare_item,
)
from reports.pdf_export import export_invoice
from ui.clients_dialog import ClientsDialog
from ui.history_dialog import HistoryDialog
from ui.item_dialog import ItemDialog
from ui.theme import polish_table, set_button_icon, set_button_role, set_surface, set_variant


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_invoice_id = None
        self.current_client_id = None
        self.current_vehicle_id = None
        self._loading_customer = False

        self.setWindowTitle("AutoService — Акти виконаних робіт")
        self.setWindowIcon(app_icon())
        self.resize(1180, 980)
        self.setMinimumSize(980, 760)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll_area)
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 16, 20, 16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        logo_label = QLabel()
        logo_label.setFixedSize(46, 46)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pixmap = QPixmap(str(resource_path("assets", "logo.png")))
        if not logo_pixmap.isNull():
            logo_label.setPixmap(
                logo_pixmap.scaled(
                    42,
                    42,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        title_label = QLabel("AutoService")
        set_variant(title_label, "title")
        subtitle_label = QLabel("Акти виконаних робіт, клієнти та історія сервісу")
        set_variant(subtitle_label, "subtitle")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        lookup_panel = QFrame()
        set_surface(lookup_panel)
        lookup_panel_layout = QVBoxLayout(lookup_panel)
        lookup_panel_layout.setSpacing(10)
        lookup_panel_layout.setContentsMargins(16, 14, 16, 14)

        lookup_title = QLabel("Пошук клієнта або автомобіля")
        set_variant(lookup_title, "section")
        lookup_panel_layout.addWidget(lookup_title)

        lookup_layout = QHBoxLayout()
        lookup_layout.setSpacing(10)
        self.lookupEdit = QLineEdit()
        self.lookupEdit.setPlaceholderText("ПІБ, телефон, VIN або держномер")
        self.lookupButton = QPushButton("Знайти")
        set_button_role(self.lookupButton, "primary")
        set_button_icon(self.lookupButton, QStyle.StandardPixmap.SP_FileDialogContentsView)
        lookup_layout.addWidget(self.lookupEdit, 2)
        lookup_layout.addWidget(self.lookupButton)
        lookup_panel_layout.addLayout(lookup_layout)

        lookup_result_layout = QHBoxLayout()
        lookup_result_layout.setSpacing(10)
        self.lookupCombo = QComboBox()
        self.lookupCombo.setMinimumWidth(520)
        self.lookupCombo.setMinimumHeight(32)
        self.applyLookupButton = QPushButton("Обрати")
        set_button_role(self.applyLookupButton, "success")
        set_button_icon(self.applyLookupButton, QStyle.StandardPixmap.SP_DialogApplyButton)
        self.clearCustomerButton = QPushButton("Очистити вибір")
        set_button_role(self.clearCustomerButton, "subtle")
        set_button_icon(self.clearCustomerButton, QStyle.StandardPixmap.SP_DialogResetButton)
        lookup_result_layout.addWidget(self.lookupCombo, 1)
        lookup_result_layout.addWidget(self.applyLookupButton)
        lookup_result_layout.addWidget(self.clearCustomerButton)
        lookup_panel_layout.addLayout(lookup_result_layout)

        self.selectedCustomerLabel = QLabel("Новий клієнт / автомобіль")
        set_variant(self.selectedCustomerLabel, "muted")
        lookup_panel_layout.addWidget(self.selectedCustomerLabel)
        main_layout.addWidget(lookup_panel)

        details_panel = QFrame()
        set_surface(details_panel)
        details_panel.setMinimumHeight(168)
        details_layout = QVBoxLayout(details_panel)
        details_layout.setSpacing(12)
        details_layout.setContentsMargins(16, 14, 16, 14)

        details_title = QLabel("Дані акту")
        set_variant(details_title, "section")
        details_layout.addWidget(details_title)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(18)
        form_grid.setVerticalSpacing(9)
        form_grid.setColumnStretch(1, 1)
        form_grid.setColumnStretch(3, 1)

        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(QDate.currentDate())

        self.clientEdit = QLineEdit()
        self.clientEdit.setPlaceholderText("Приклад: Іванов Петро Сидорович")
        self.phoneEdit = QLineEdit()
        self.phoneEdit.setPlaceholderText("+380...")
        self.brandEdit = QLineEdit()
        self.brandEdit.setPlaceholderText("Наприклад: BMW")
        self.modelEdit = QLineEdit()
        self.modelEdit.setPlaceholderText("Наприклад: X5")
        self.vinEdit = QLineEdit()
        self.vinEdit.setPlaceholderText("VIN-код")
        self.numberEdit = QLineEdit()
        self.numberEdit.setPlaceholderText("Наприклад: AA1234AA")
        self.mileageEdit = QLineEdit()
        self.mileageEdit.setPlaceholderText("Наприклад: 185000")

        form_fields = (
            self.dateEdit,
            self.clientEdit,
            self.phoneEdit,
            self.brandEdit,
            self.modelEdit,
            self.vinEdit,
            self.numberEdit,
            self.mileageEdit,
        )
        for field in form_fields:
            field.setMinimumHeight(32)
            field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        detail_rows = (
            ("Дата:", self.dateEdit, "Марка авто:", self.brandEdit),
            ("ПІБ клієнта:", self.clientEdit, "Модель авто:", self.modelEdit),
            ("Телефон:", self.phoneEdit, "VIN-код:", self.vinEdit),
            ("Пробіг (км):", self.mileageEdit, "Держномер:", self.numberEdit),
        )
        for row, (left_label, left_widget, right_label, right_widget) in enumerate(detail_rows):
            left = QLabel(left_label)
            right = QLabel(right_label)
            left.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            form_grid.addWidget(left, row, 0)
            form_grid.addWidget(left_widget, row, 1)
            form_grid.addWidget(right, row, 2)
            form_grid.addWidget(right_widget, row, 3)
        details_layout.addLayout(form_grid)
        main_layout.addWidget(details_panel)

        materials_panel = QFrame()
        set_surface(materials_panel)
        materials_layout = QVBoxLayout(materials_panel)
        materials_layout.setSpacing(10)
        materials_layout.setContentsMargins(16, 14, 16, 14)

        materials_header = QHBoxLayout()
        lbl_materials = QLabel("Матеріали та запчастини")
        set_variant(lbl_materials, "section")
        self.addMaterialButton = QPushButton("Додати матеріал")
        set_button_role(self.addMaterialButton, "subtle")
        set_button_icon(self.addMaterialButton, QStyle.StandardPixmap.SP_FileDialogNewFolder)
        materials_header.addWidget(lbl_materials)
        materials_header.addStretch()
        materials_header.addWidget(self.addMaterialButton)
        materials_layout.addLayout(materials_header)

        self.materialsTable = QTableWidget(0, 5)
        self.materialsTable.setHorizontalHeaderLabels(["Назва", "Кількість", "Ціна", "Знижка", "Сума"])
        self.materialsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        polish_table(self.materialsTable)
        self.materialsTable.setMinimumHeight(118)
        self.setup_table_headers(self.materialsTable)
        materials_layout.addWidget(self.materialsTable)
        (
            materials_discount_layout,
            self.materialsDiscountTypeCombo,
            self.materialsDiscountValueSpin,
        ) = self.create_discount_controls("Знижка на матеріали")
        materials_layout.addLayout(materials_discount_layout)
        main_layout.addWidget(materials_panel, 1)

        works_panel = QFrame()
        set_surface(works_panel)
        works_layout = QVBoxLayout(works_panel)
        works_layout.setSpacing(10)
        works_layout.setContentsMargins(16, 14, 16, 14)

        works_header = QHBoxLayout()
        lbl_works = QLabel("Послуги та роботи")
        set_variant(lbl_works, "section")
        self.addWorkButton = QPushButton("Додати послугу")
        set_button_role(self.addWorkButton, "subtle")
        set_button_icon(self.addWorkButton, QStyle.StandardPixmap.SP_FileDialogNewFolder)
        works_header.addWidget(lbl_works)
        works_header.addStretch()
        works_header.addWidget(self.addWorkButton)
        works_layout.addLayout(works_header)

        self.worksTable = QTableWidget(0, 5)
        self.worksTable.setHorizontalHeaderLabels(["Назва", "Кількість", "Ціна", "Знижка", "Сума"])
        self.worksTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        polish_table(self.worksTable)
        self.worksTable.setMinimumHeight(118)
        self.setup_table_headers(self.worksTable)
        works_layout.addWidget(self.worksTable)
        (
            works_discount_layout,
            self.worksDiscountTypeCombo,
            self.worksDiscountValueSpin,
        ) = self.create_discount_controls("Знижка на послуги")
        works_layout.addLayout(works_discount_layout)
        main_layout.addWidget(works_panel, 1)

        footer_panel = QFrame()
        set_surface(footer_panel)
        footer_layout = QVBoxLayout(footer_panel)
        footer_layout.setSpacing(12)
        footer_layout.setContentsMargins(16, 14, 16, 14)

        (
            invoice_discount_layout,
            self.invoiceDiscountTypeCombo,
            self.invoiceDiscountValueSpin,
        ) = self.create_discount_controls("Загальна знижка на акт")
        footer_layout.addLayout(invoice_discount_layout)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(16)

        self.materialsTotal = QLabel("Матеріали: 0.00 грн")
        self.worksTotal = QLabel("Послуги: 0.00 грн")
        self.discountTotal = QLabel("Знижки: 0.00 грн")
        self.totalLabel = QLabel("РАЗОМ ДО ОПЛАТИ: 0.00 грн")
        set_variant(self.materialsTotal, "muted")
        set_variant(self.worksTotal, "muted")
        set_variant(self.discountTotal, "muted")
        set_variant(self.totalLabel, "summary")

        summary_layout.addWidget(self.materialsTotal)
        summary_layout.addWidget(self.worksTotal)
        summary_layout.addWidget(self.discountTotal)
        summary_layout.addStretch()
        summary_layout.addWidget(self.totalLabel)
        footer_layout.addLayout(summary_layout)

        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(10)
        self.btn_new = QPushButton("Новий акт")
        self.btn_clients = QPushButton("Клієнти")
        self.btn_history = QPushButton("Журнал актів")
        self.btn_save = QPushButton("Зберегти")
        self.pdfButton = QPushButton("Сформувати PDF")
        set_button_role(self.btn_new, "subtle")
        set_button_role(self.btn_clients, "subtle")
        set_button_role(self.btn_history, "subtle")
        set_button_role(self.btn_save, "success")
        set_button_role(self.pdfButton, "primary")
        set_button_icon(self.btn_new, QStyle.StandardPixmap.SP_FileDialogNewFolder)
        set_button_icon(self.btn_clients, QStyle.StandardPixmap.SP_DirIcon)
        set_button_icon(self.btn_history, QStyle.StandardPixmap.SP_FileDialogDetailedView)
        set_button_icon(self.btn_save, QStyle.StandardPixmap.SP_DialogSaveButton)
        set_button_icon(self.pdfButton, QStyle.StandardPixmap.SP_FileIcon)

        action_buttons.addWidget(self.btn_new)
        action_buttons.addWidget(self.btn_clients)
        action_buttons.addWidget(self.btn_history)
        action_buttons.addStretch()
        action_buttons.addWidget(self.btn_save)
        action_buttons.addWidget(self.pdfButton)
        footer_layout.addLayout(action_buttons)
        main_layout.addWidget(footer_panel)

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
        self.materialsTable.itemDoubleClicked.connect(lambda _item: self.edit_selected_item(self.materialsTable))
        self.worksTable.itemDoubleClicked.connect(lambda _item: self.edit_selected_item(self.worksTable))

        self.refresh_customer_lookup()
        self.calculate_totals()

    def create_discount_controls(self, label_text):
        layout = QHBoxLayout()
        layout.setSpacing(10)

        label = QLabel(label_text)
        set_variant(label, "muted")

        type_combo = QComboBox()
        type_combo.addItem("Без знижки", DISCOUNT_NONE)
        type_combo.addItem("Відсоток", DISCOUNT_PERCENT)
        type_combo.addItem("Сума, грн", DISCOUNT_AMOUNT)
        type_combo.setMinimumWidth(135)

        value_spin = QDoubleSpinBox()
        value_spin.setDecimals(2)
        value_spin.setMaximum(1000000)
        value_spin.setMinimumWidth(130)

        type_combo.currentIndexChanged.connect(
            lambda _index, combo=type_combo, spin=value_spin: self.on_discount_type_changed(combo, spin)
        )
        value_spin.valueChanged.connect(
            lambda _value: self.calculate_totals() if hasattr(self, "totalLabel") else None
        )

        layout.addWidget(label)
        layout.addWidget(type_combo)
        layout.addWidget(value_spin)
        layout.addStretch()

        self.on_discount_type_changed(type_combo, value_spin)
        return layout, type_combo, value_spin

    def on_discount_type_changed(self, combo: QComboBox, spin: QDoubleSpinBox):
        discount_type = combo.currentData()
        enabled = discount_type != DISCOUNT_NONE
        spin.setEnabled(enabled)
        if discount_type == DISCOUNT_PERCENT:
            spin.setMaximum(100)
            spin.setSuffix(" %")
        else:
            spin.setMaximum(1000000)
            spin.setSuffix(" грн")
        if not enabled:
            spin.setValue(0)
        if hasattr(self, "totalLabel"):
            self.calculate_totals()

    def get_discount_control_data(self, combo: QComboBox, spin: QDoubleSpinBox):
        discount_type = combo.currentData()
        return {
            "discount_type": discount_type,
            "discount_value": spin.value() if discount_type != DISCOUNT_NONE else 0.0,
        }

    def set_discount_control_data(self, combo: QComboBox, spin: QDoubleSpinBox, discount_type, discount_value):
        discount_type = normalize_discount_type(discount_type)
        index = combo.findData(discount_type)
        combo.setCurrentIndex(index if index >= 0 else 0)
        spin.setValue(float(discount_value or 0))
        self.on_discount_type_changed(combo, spin)

    def reset_discount_controls(self):
        self.set_discount_control_data(self.materialsDiscountTypeCombo, self.materialsDiscountValueSpin, DISCOUNT_NONE, 0)
        self.set_discount_control_data(self.worksDiscountTypeCombo, self.worksDiscountValueSpin, DISCOUNT_NONE, 0)
        self.set_discount_control_data(self.invoiceDiscountTypeCombo, self.invoiceDiscountValueSpin, DISCOUNT_NONE, 0)

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

    def _table_item_data(self, table: QTableWidget, row: int) -> dict:
        name_item = table.item(row, 0)
        if name_item:
            data = name_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                return dict(data)

        return prepare_item({
            "name": name_item.text() if name_item else "",
            "qty": table.item(row, 1).text() if table.item(row, 1) else 0,
            "price": table.item(row, 2).text() if table.item(row, 2) else 0,
            "discount_type": DISCOUNT_NONE,
            "discount_value": 0,
        })

    def _set_table_row(self, table: QTableWidget, row: int, item_data: dict):
        item = prepare_item(item_data)
        values = [
            str(item.get("name", "")),
            f"{item['qty']:g}",
            f"{item['price']:.2f}",
            format_discount(item.get("discount_type"), item.get("discount_value")),
            f"{item['sum']:.2f}",
        ]

        for column, value in enumerate(values):
            table_item = QTableWidgetItem(value)
            if column in (1, 2, 3, 4):
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if column == 0:
                table_item.setData(Qt.ItemDataRole.UserRole, item)
            table.setItem(row, column, table_item)

    def _add_table_item(self, table: QTableWidget, item_data: dict):
        row = table.rowCount()
        table.insertRow(row)
        self._set_table_row(table, row, item_data)
        self.calculate_totals()

    def _collect_table_items(self, table: QTableWidget) -> list[dict]:
        return [self._table_item_data(table, row) for row in range(table.rowCount())]

    def edit_selected_item(self, table: QTableWidget):
        row = table.currentRow()
        if row < 0:
            return

        title = "Матеріал" if table is self.materialsTable else "Послуга"
        dialog = ItemDialog(title, self._table_item_data(table, row))
        if dialog.exec():
            self._set_table_row(table, row, dialog.get_data())
            self.calculate_totals()

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
            "materials_discount_type": self.materialsDiscountTypeCombo.currentData(),
            "materials_discount_value": (
                self.materialsDiscountValueSpin.value()
                if self.materialsDiscountTypeCombo.currentData() != DISCOUNT_NONE
                else 0.0
            ),
            "works_discount_type": self.worksDiscountTypeCombo.currentData(),
            "works_discount_value": (
                self.worksDiscountValueSpin.value()
                if self.worksDiscountTypeCombo.currentData() != DISCOUNT_NONE
                else 0.0
            ),
            "invoice_discount_type": self.invoiceDiscountTypeCombo.currentData(),
            "invoice_discount_value": (
                self.invoiceDiscountValueSpin.value()
                if self.invoiceDiscountTypeCombo.currentData() != DISCOUNT_NONE
                else 0.0
            ),
        }

        materials = self._collect_table_items(self.materialsTable)
        works = self._collect_table_items(self.worksTable)

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
        self.reset_discount_controls()

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
        self.set_discount_control_data(
            self.materialsDiscountTypeCombo,
            self.materialsDiscountValueSpin,
            vehicle.get("materials_discount_type"),
            vehicle.get("materials_discount_value"),
        )
        self.set_discount_control_data(
            self.worksDiscountTypeCombo,
            self.worksDiscountValueSpin,
            vehicle.get("works_discount_type"),
            vehicle.get("works_discount_value"),
        )
        self.set_discount_control_data(
            self.invoiceDiscountTypeCombo,
            self.invoiceDiscountValueSpin,
            vehicle.get("invoice_discount_type"),
            vehicle.get("invoice_discount_value"),
        )
        self._loading_customer = False

        self.materialsTable.setRowCount(0)
        for row, item in enumerate(materials):
            self.materialsTable.insertRow(row)
            self._set_table_row(self.materialsTable, row, item)

        self.worksTable.setRowCount(0)
        for row, item in enumerate(works):
            self.worksTable.insertRow(row)
            self._set_table_row(self.worksTable, row, item)

        self.calculate_totals()
        self.update_customer_label()
        self.setWindowTitle(f"AutoService — РЕДАГУВАННЯ АКТУ №{invoice_id}")

    def setup_table_headers(self, table: QTableWidget):
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

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
        vehicle = {
            "materials_discount_type": self.materialsDiscountTypeCombo.currentData(),
            "materials_discount_value": self.materialsDiscountValueSpin.value(),
            "works_discount_type": self.worksDiscountTypeCombo.currentData(),
            "works_discount_value": self.worksDiscountValueSpin.value(),
            "invoice_discount_type": self.invoiceDiscountTypeCombo.currentData(),
            "invoice_discount_value": self.invoiceDiscountValueSpin.value(),
        }
        totals = calculate_invoice_totals(
            vehicle,
            self._collect_table_items(self.materialsTable),
            self._collect_table_items(self.worksTable),
        )

        self.materialsTotal.setText(f"Матеріали: {totals['materials_total']:.2f} грн")
        self.worksTotal.setText(f"Послуги: {totals['works_total']:.2f} грн")
        discount_prefix = "-" if totals["discount_total"] > 0 else ""
        self.discountTotal.setText(f"Знижки: {discount_prefix}{totals['discount_total']:.2f} грн")
        self.totalLabel.setText(f"РАЗОМ ДО ОПЛАТИ: {totals['total']:.2f} грн")

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
            self._add_table_item(self.materialsTable, dialog.get_data())

    def add_work(self):
        dialog = ItemDialog("Послуга")
        if dialog.exec():
            self._add_table_item(self.worksTable, dialog.get_data())

    def table_key_press(self, event, table: QTableWidget):
        if event.key() == Qt.Key_Delete:
            selected_rows = sorted(set(index.row() for index in table.selectedIndexes()), reverse=True)
            if selected_rows:
                for row in selected_rows:
                    table.removeRow(row)
                self.calculate_totals()
        else:
            QTableWidget.keyPressEvent(table, event)
