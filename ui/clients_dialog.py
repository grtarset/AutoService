from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from database.db_manager import delete_client, get_client_card, get_clients
from ui.client_card_dialog import ClientCardDialog


class ClientsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_record = None

        self.setWindowTitle("Журнал клієнтів")
        self.resize(980, 560)

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Пошук: клієнт, телефон, авто, VIN або держномер")
        self.clearSearchButton = QPushButton("Очистити")
        search_layout.addWidget(self.searchEdit, 1)
        search_layout.addWidget(self.clearSearchButton)
        layout.addLayout(search_layout)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Клієнт",
            "Основний телефон",
            "Усі телефони",
            "Автомобілі",
            "Авто",
            "Акти",
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.setup_headers()
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.newButton = QPushButton("Новий клієнт")
        self.editButton = QPushButton("Редагувати картку")
        self.deleteButton = QPushButton("Видалити")
        self.selectButton = QPushButton("Обрати для акту")
        self.closeButton = QPushButton("Закрити")
        buttons.addWidget(self.newButton)
        buttons.addWidget(self.editButton)
        buttons.addWidget(self.deleteButton)
        buttons.addStretch()
        buttons.addWidget(self.selectButton)
        buttons.addWidget(self.closeButton)
        layout.addLayout(buttons)

        self.searchEdit.textChanged.connect(self.load_data)
        self.clearSearchButton.clicked.connect(self.searchEdit.clear)
        self.newButton.clicked.connect(self.create_client)
        self.editButton.clicked.connect(self.edit_selected_client)
        self.deleteButton.clicked.connect(self.delete_selected_client)
        self.selectButton.clicked.connect(self.select_for_invoice)
        self.closeButton.clicked.connect(self.reject)
        self.table.itemDoubleClicked.connect(lambda _item: self.edit_selected_client())

        self.load_data()

    def setup_headers(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

    def load_data(self, _text=None):
        selected_id = self.get_selected_id()
        self.table.setRowCount(0)

        clients = get_clients(self.searchEdit.text())
        selected_row = 0
        for row, client in enumerate(clients):
            self.table.insertRow(row)
            values = [
                client["id"],
                client.get("name", ""),
                client.get("primary_phone", ""),
                client.get("phones", ""),
                client.get("vehicles", ""),
                client.get("vehicle_count", 0),
                client.get("invoice_count", 0),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value or "")))
            if selected_id and client["id"] == selected_id:
                selected_row = row

        if self.table.rowCount() > 0:
            self.table.selectRow(selected_row)

    def get_selected_id(self):
        row = self.table.currentRow()
        if row >= 0 and self.table.item(row, 0):
            return int(self.table.item(row, 0).text())
        return None

    def create_client(self):
        dialog = ClientCardDialog(parent=self)
        if dialog.exec():
            self.load_data()
            self.select_client_id(dialog.get_client_id())

    def edit_selected_client(self):
        client_id = self.get_selected_id()
        if not client_id:
            return

        dialog = ClientCardDialog(client_id, self)
        if dialog.exec():
            self.load_data()
            self.select_client_id(client_id)

    def delete_selected_client(self):
        client_id = self.get_selected_id()
        if not client_id:
            return

        reply = QMessageBox.question(
            self,
            "Видалення клієнта",
            "Видалити картку клієнта? Старі акти залишаться, але зв'язок із карткою буде прибрано.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_client(client_id)
            self.load_data()

    def select_client_id(self, client_id):
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 0).text()) == client_id:
                self.table.selectRow(row)
                return

    def select_for_invoice(self):
        client_id = self.get_selected_id()
        if not client_id:
            return

        card = get_client_card(client_id)
        client = card["client"]
        vehicle = card["vehicles"][0] if card["vehicles"] else {}
        self.selected_record = {
            "client_id": client_id,
            "client": client.get("name", ""),
            "phone": client.get("phone", ""),
            "vehicle_id": vehicle.get("id"),
            "brand": vehicle.get("brand", ""),
            "model": vehicle.get("model", ""),
            "vin": vehicle.get("vin", ""),
            "number": vehicle.get("number", ""),
            "mileage": vehicle.get("mileage", ""),
        }
        self.accept()

    def get_selected_record(self):
        return self.selected_record
