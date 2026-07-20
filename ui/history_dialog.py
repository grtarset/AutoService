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

from database.db_manager import delete_invoice, get_all_invoices


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Журнал актів")
        self.resize(940, 500)

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Пошук: клієнт, телефон, авто, VIN, держномер або дата")
        self.btn_clear_search = QPushButton("Очистити")
        search_layout.addWidget(self.searchEdit, 1)
        search_layout.addWidget(self.btn_clear_search)
        layout.addLayout(search_layout)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Дата",
            "Клієнт",
            "Телефон",
            "Автомобіль",
            "Держномер",
            "VIN",
            "Сума",
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.setup_headers()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("✏️ Редагувати")
        self.btn_delete = QPushButton("❌ Видалити")
        self.btn_close = QPushButton("Закрити")

        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_edit.clicked.connect(self.accept_selected)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_close.clicked.connect(self.reject)
        self.btn_clear_search.clicked.connect(self.searchEdit.clear)
        self.searchEdit.textChanged.connect(self.load_data)
        self.table.itemDoubleClicked.connect(lambda _item: self.accept_selected())

        self.load_data()

    def setup_headers(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

    def load_data(self, _text=None):
        self.table.setRowCount(0)
        invoices = get_all_invoices(self.searchEdit.text())
        for row, invoice in enumerate(invoices):
            self.table.insertRow(row)
            invoice_id, date, client, phone, brand, model, number, vin, total = invoice
            values = [
                str(invoice_id),
                date or "",
                client or "",
                phone or "",
                f"{brand or ''} {model or ''}".strip(),
                number or "",
                vin or "",
                f"{total:.2f} грн",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(0, value)
                self.table.setItem(row, column, item)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            return int(self.table.item(selected_row, 0).text())
        return None

    def accept_selected(self):
        if self.get_selected_id():
            self.accept()

    def on_delete(self):
        invoice_id = self.get_selected_id()
        if not invoice_id:
            return

        reply = QMessageBox.question(
            self,
            "Видалення",
            f"Ви дійсно хочете видалити акт №{invoice_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            delete_invoice(invoice_id)
            self.load_data()
