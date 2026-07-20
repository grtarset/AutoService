from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from database.db_manager import get_client_card, save_client_card


class ClientCardDialog(QDialog):
    def __init__(self, client_id=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self._updating_primary = False

        self.setWindowTitle("Картка клієнта")
        self.resize(860, 640)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.notesEdit = QPlainTextEdit()
        self.notesEdit.setFixedHeight(70)
        form_layout.addRow("ПІБ / Назва:", self.nameEdit)
        form_layout.addRow("Примітки:", self.notesEdit)
        layout.addLayout(form_layout)

        layout.addWidget(QLabel("<b>Телефони</b>"))
        self.phonesTable = QTableWidget(0, 4)
        self.phonesTable.setHorizontalHeaderLabels(["ID", "Тип", "Телефон", "Основний"])
        self.phonesTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.phonesTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.phonesTable.verticalHeader().setVisible(False)
        self.phonesTable.setColumnHidden(0, True)
        self.phonesTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.phonesTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.phonesTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.phonesTable.itemChanged.connect(self.on_phone_item_changed)
        layout.addWidget(self.phonesTable)

        phone_buttons = QHBoxLayout()
        self.addPhoneButton = QPushButton("Додати телефон")
        self.deletePhoneButton = QPushButton("Видалити телефон")
        phone_buttons.addWidget(self.addPhoneButton)
        phone_buttons.addWidget(self.deletePhoneButton)
        phone_buttons.addStretch()
        layout.addLayout(phone_buttons)

        layout.addWidget(QLabel("<b>Автомобілі</b>"))
        self.vehiclesTable = QTableWidget(0, 7)
        self.vehiclesTable.setHorizontalHeaderLabels([
            "ID",
            "Марка",
            "Модель",
            "VIN",
            "Держномер",
            "Пробіг",
            "Примітки",
        ])
        self.vehiclesTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vehiclesTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.vehiclesTable.verticalHeader().setVisible(False)
        self.vehiclesTable.setColumnHidden(0, True)
        self.vehiclesTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.vehiclesTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.vehiclesTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.vehiclesTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.vehiclesTable.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.vehiclesTable.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        layout.addWidget(self.vehiclesTable)

        vehicle_buttons = QHBoxLayout()
        self.addVehicleButton = QPushButton("Додати автомобіль")
        self.deleteVehicleButton = QPushButton("Видалити автомобіль")
        vehicle_buttons.addWidget(self.addVehicleButton)
        vehicle_buttons.addWidget(self.deleteVehicleButton)
        vehicle_buttons.addStretch()
        layout.addLayout(vehicle_buttons)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)

        self.addPhoneButton.clicked.connect(self.add_phone_row)
        self.deletePhoneButton.clicked.connect(self.delete_selected_phone)
        self.addVehicleButton.clicked.connect(self.add_vehicle_row)
        self.deleteVehicleButton.clicked.connect(self.delete_selected_vehicle)
        self.buttons.accepted.connect(self.save_and_accept)
        self.buttons.rejected.connect(self.reject)

        if client_id:
            self.load_client(client_id)
        else:
            self.add_phone_row(is_primary=True)
            self.add_vehicle_row()

    def load_client(self, client_id):
        card = get_client_card(client_id)
        client = card["client"]
        self.nameEdit.setText(client.get("name") or "")
        self.notesEdit.setPlainText(client.get("notes") or "")

        self.phonesTable.setRowCount(0)
        for phone in card["phones"]:
            self.add_phone_row(phone)
        if self.phonesTable.rowCount() == 0:
            self.add_phone_row(is_primary=True)

        self.vehiclesTable.setRowCount(0)
        for vehicle in card["vehicles"]:
            self.add_vehicle_row(vehicle)
        if self.vehiclesTable.rowCount() == 0:
            self.add_vehicle_row()

    def _set_item(self, table, row, column, value):
        table.setItem(row, column, QTableWidgetItem(str(value or "")))

    def add_phone_row(self, phone=None, is_primary=False):
        row = self.phonesTable.rowCount()
        self.phonesTable.insertRow(row)

        if phone is None:
            phone = {
                "id": "",
                "label": "Основний" if is_primary else "Додатковий",
                "phone": "",
                "is_primary": is_primary,
            }

        self._set_item(self.phonesTable, row, 0, phone.get("id"))
        self._set_item(self.phonesTable, row, 1, phone.get("label"))
        self._set_item(self.phonesTable, row, 2, phone.get("phone"))

        primary_item = QTableWidgetItem()
        primary_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        primary_item.setCheckState(Qt.Checked if phone.get("is_primary") else Qt.Unchecked)
        self.phonesTable.setItem(row, 3, primary_item)

    def delete_selected_phone(self):
        row = self.phonesTable.currentRow()
        if row >= 0:
            was_primary = self.phonesTable.item(row, 3).checkState() == Qt.Checked
            self.phonesTable.removeRow(row)
            if was_primary and self.phonesTable.rowCount() > 0:
                self.phonesTable.item(0, 3).setCheckState(Qt.Checked)

    def on_phone_item_changed(self, item):
        if self._updating_primary or item.column() != 3 or item.checkState() != Qt.Checked:
            return

        self._updating_primary = True
        for row in range(self.phonesTable.rowCount()):
            if row != item.row():
                self.phonesTable.item(row, 3).setCheckState(Qt.Unchecked)
        self._updating_primary = False

    def add_vehicle_row(self, vehicle=None):
        row = self.vehiclesTable.rowCount()
        self.vehiclesTable.insertRow(row)
        vehicle = vehicle or {}
        values = [
            vehicle.get("id", ""),
            vehicle.get("brand", ""),
            vehicle.get("model", ""),
            vehicle.get("vin", ""),
            vehicle.get("number", ""),
            vehicle.get("mileage", ""),
            vehicle.get("notes", ""),
        ]
        for column, value in enumerate(values):
            self._set_item(self.vehiclesTable, row, column, value)

    def delete_selected_vehicle(self):
        row = self.vehiclesTable.currentRow()
        if row >= 0:
            self.vehiclesTable.removeRow(row)

    def collect_phones(self):
        phones = []
        for row in range(self.phonesTable.rowCount()):
            phone = self.phonesTable.item(row, 2).text().strip() if self.phonesTable.item(row, 2) else ""
            if not phone:
                continue
            phone_id = self.phonesTable.item(row, 0).text().strip() if self.phonesTable.item(row, 0) else ""
            phones.append({
                "id": int(phone_id) if phone_id else None,
                "label": self.phonesTable.item(row, 1).text().strip() if self.phonesTable.item(row, 1) else "",
                "phone": phone,
                "is_primary": self.phonesTable.item(row, 3).checkState() == Qt.Checked,
            })
        return phones

    def collect_vehicles(self):
        vehicles = []
        for row in range(self.vehiclesTable.rowCount()):
            vehicle_id = self.vehiclesTable.item(row, 0).text().strip() if self.vehiclesTable.item(row, 0) else ""
            vehicle = {
                "id": int(vehicle_id) if vehicle_id else None,
                "brand": self.vehiclesTable.item(row, 1).text().strip() if self.vehiclesTable.item(row, 1) else "",
                "model": self.vehiclesTable.item(row, 2).text().strip() if self.vehiclesTable.item(row, 2) else "",
                "vin": self.vehiclesTable.item(row, 3).text().strip() if self.vehiclesTable.item(row, 3) else "",
                "number": self.vehiclesTable.item(row, 4).text().strip() if self.vehiclesTable.item(row, 4) else "",
                "mileage": self.vehiclesTable.item(row, 5).text().strip() if self.vehiclesTable.item(row, 5) else "",
                "notes": self.vehiclesTable.item(row, 6).text().strip() if self.vehiclesTable.item(row, 6) else "",
            }
            if any(value for key, value in vehicle.items() if key != "id"):
                vehicles.append(vehicle)
        return vehicles

    def save_and_accept(self):
        name = self.nameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, "Картка клієнта", "Вкажіть ПІБ або назву клієнта.")
            return

        client = {
            "id": self.client_id,
            "name": name,
            "notes": self.notesEdit.toPlainText().strip(),
        }

        try:
            self.client_id = save_client_card(client, self.collect_phones(), self.collect_vehicles())
        except Exception as error:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти картку клієнта: {error}")
            return

        self.accept()

    def get_client_id(self):
        return self.client_id
