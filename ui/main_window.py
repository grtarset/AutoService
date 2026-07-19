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
    QApplication
)

from PySide6.QtCore import QDate
from ui.item_dialog import ItemDialog
from reports.pdf_export import export_invoice


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoService")
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        #####################################################
        # Дані автомобіля
        #####################################################

        form = QFormLayout()

        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(QDate.currentDate())

        self.brandEdit = QLineEdit()
        self.modelEdit = QLineEdit()
        self.vinEdit = QLineEdit()
        self.numberEdit = QLineEdit()
        self.mileageEdit = QLineEdit()

        form.addRow("Дата", self.dateEdit)
        form.addRow("Марка", self.brandEdit)
        form.addRow("Модель", self.modelEdit)
        form.addRow("VIN", self.vinEdit)
        form.addRow("Держномер", self.numberEdit)
        form.addRow("Пробіг", self.mileageEdit)

        layout.addLayout(form)

        #####################################################
        # Матеріали
        #####################################################

        layout.addWidget(QLabel("Матеріали"))

        self.materialsTable = QTableWidget(0, 4)

        self.materialsTable.setHorizontalHeaderLabels(
            [
                "Назва",
                "Кількість",
                "Ціна",
                "Сума"
            ]
        )

        self.materialsTable.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        layout.addWidget(self.materialsTable)

        btnLayout = QHBoxLayout()

        self.addMaterialButton = QPushButton("Додати матеріал")

        btnLayout.addWidget(self.addMaterialButton)

        layout.addLayout(btnLayout)

        #####################################################
        # Роботи
        #####################################################

        layout.addWidget(QLabel("Послуги"))

        self.worksTable = QTableWidget(0, 4)

        self.worksTable.setHorizontalHeaderLabels(
            [
                "Назва",
                "Кількість",
                "Ціна",
                "Сума"
            ]
        )

        self.worksTable.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        layout.addWidget(self.worksTable)

        btnLayout2 = QHBoxLayout()

        self.addWorkButton = QPushButton("Додати послугу")

        btnLayout2.addWidget(self.addWorkButton)

        layout.addLayout(btnLayout2)

        #####################################################
        # Підсумки
        #####################################################

        self.materialsTotal = QLabel("Матеріали: 0 грн")
        self.worksTotal = QLabel("Послуги: 0 грн")
        self.totalLabel = QLabel("ВСЬОГО: 0 грн")

        layout.addWidget(self.materialsTotal)
        layout.addWidget(self.worksTotal)
        layout.addWidget(self.totalLabel)

        #####################################################
        # Кнопки
        #####################################################

        buttons = QHBoxLayout()

        self.pdfButton = QPushButton("Створити PDF")

        buttons.addStretch()
        buttons.addWidget(self.pdfButton)

        layout.addLayout(buttons)

        self.addMaterialButton.clicked.connect(self.add_material)
        self.addWorkButton.clicked.connect(self.add_work)

        self.pdfButton.clicked.connect(self.create_pdf)

def create_pdf(self):

    vehicle = {
        "date": self.dateEdit.date().toString("dd.MM.yyyy"),
        "brand": self.brandEdit.text(),
        "model": self.modelEdit.text(),
        "vin": self.vinEdit.text(),
        "number": self.numberEdit.text(),
        "mileage": self.mileageEdit.text()
    }

    materials = []

    for row in range(self.materialsTable.rowCount()):

        qty = float(self.materialsTable.item(row,1).text())
        price = float(self.materialsTable.item(row,2).text())

        materials.append({

            "name": self.materialsTable.item(row,0).text(),
            "qty": qty,
            "price": price,
            "sum": qty * price

        })

    works = []

    for row in range(self.worksTable.rowCount()):

        qty = float(self.worksTable.item(row,1).text())
        price = float(self.worksTable.item(row,2).text())

        works.append({

            "name": self.worksTable.item(row,0).text(),
            "qty": qty,
            "price": price,
            "sum": qty * price

        })

    export_invoice(
        "invoice.pdf",
        vehicle,
        materials,
        works
    )

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


def calculate_totals(self):

    materials = 0

    for row in range(self.materialsTable.rowCount()):
        materials += float(
            self.materialsTable.item(row, 3).text()
        )

    works = 0

    for row in range(self.worksTable.rowCount()):
        works += float(
            self.worksTable.item(row, 3).text()
        )

    self.materialsTotal.setText(f"Матеріали: {materials:.2f} грн")
    self.worksTotal.setText(f"Послуги: {works:.2f} грн")
    self.totalLabel.setText(f"ВСЬОГО: {materials + works:.2f} грн")