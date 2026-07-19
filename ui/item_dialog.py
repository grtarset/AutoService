from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
    QPushButton,
    QHBoxLayout
)


class ItemDialog(QDialog):

    def __init__(self, title):
        super().__init__()

        self.setWindowTitle(title)
        
        # Встановлюємо комфортну ширину (600 пікселів) та висоту (180 пікселів)
        self.resize(600, 180) 

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.nameEdit = QLineEdit()

        self.qtySpin = QDoubleSpinBox()
        self.qtySpin.setDecimals(2)
        self.qtySpin.setValue(1)

        self.priceSpin = QDoubleSpinBox()
        self.priceSpin.setMaximum(1000000)

        form.addRow("Назва", self.nameEdit)
        form.addRow("Кількість", self.qtySpin)
        form.addRow("Ціна", self.priceSpin)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        ok = QPushButton("OK")
        cancel = QPushButton("Скасувати")

        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        buttons.addWidget(ok)
        buttons.addWidget(cancel)

        layout.addLayout(buttons)

    def get_data(self):
        return (
            self.nameEdit.text(),
            self.qtySpin.value(),
            self.priceSpin.value()
        )