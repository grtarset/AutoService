from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QAbstractItemView
)
from database.db_manager import get_all_invoices, delete_invoice

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Журнал накладних")
        self.resize(700, 400)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Клієнт", "Автомобіль", "Держномер"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        
        self.btn_edit.clicked.connect(self.accept)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_close.clicked.connect(self.reject)
        
        self.selected_invoice_id = None
        self.load_data()
        
    def load_data(self):
        self.table.setRowCount(0)
        invoices = get_all_invoices()
        for idx, inv in enumerate(invoices):
            self.table.insertRow(idx)
            # inv = (id, date, client, brand, model, number)
            self.table.setItem(idx, 0, QTableWidgetItem(str(inv[0])))
            self.table.setItem(idx, 1, QTableWidgetItem(inv[1]))
            self.table.setItem(idx, 2, QTableWidgetItem(inv[2]))
            self.table.setItem(idx, 3, QTableWidgetItem(f"{inv[3]} {inv[4]}"))
            self.table.setItem(idx, 4, QTableWidgetItem(inv[5]))
            
    def get_selected_id(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            return int(self.table.item(selected_row, 0).text())
        return None

    def on_delete(self):
        invoice_id = self.get_selected_id()
        if invoice_id:
            reply = QMessageBox.question(
                self, "Видалення", f"Ви дійсно хочете видалити накладну №{invoice_id}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                delete_invoice(invoice_id)
                self.load_data()