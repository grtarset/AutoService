from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
)

from models.discounts import DISCOUNT_AMOUNT, DISCOUNT_NONE, DISCOUNT_PERCENT, normalize_discount_type
from ui.theme import set_button_icon, set_button_role, set_variant


class ItemDialog(QDialog):

    def __init__(self, title, item=None):
        super().__init__()
        item = item or {}

        self.setWindowTitle(title)
        self.resize(560, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title_label = QLabel(title)
        set_variant(title_label, "section")
        layout.addWidget(title_label)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Назва позиції")

        self.qtySpin = QDoubleSpinBox()
        self.qtySpin.setDecimals(2)
        self.qtySpin.setValue(1)
        self.qtySpin.setMinimum(0.01)
        self.qtySpin.setMaximum(1000000)

        self.priceSpin = QDoubleSpinBox()
        self.priceSpin.setMaximum(1000000)
        self.priceSpin.setSuffix(" грн")

        self.discountTypeCombo = QComboBox()
        self.discountTypeCombo.addItem("Без знижки", DISCOUNT_NONE)
        self.discountTypeCombo.addItem("Відсоток", DISCOUNT_PERCENT)
        self.discountTypeCombo.addItem("Сума, грн", DISCOUNT_AMOUNT)

        self.discountValueSpin = QDoubleSpinBox()
        self.discountValueSpin.setDecimals(2)
        self.discountValueSpin.setMaximum(1000000)

        form.addRow("Назва", self.nameEdit)
        form.addRow("Кількість", self.qtySpin)
        form.addRow("Ціна", self.priceSpin)
        form.addRow("Тип знижки", self.discountTypeCombo)
        form.addRow("Знижка", self.discountValueSpin)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        ok = QPushButton("Зберегти" if item else "Додати")
        cancel = QPushButton("Скасувати")
        set_button_role(ok, "primary")
        set_button_role(cancel, "subtle")
        set_button_icon(ok, QStyle.StandardPixmap.SP_DialogApplyButton)
        set_button_icon(cancel, QStyle.StandardPixmap.SP_DialogCancelButton)

        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        self.discountTypeCombo.currentIndexChanged.connect(self.update_discount_state)

        buttons.addStretch()
        buttons.addWidget(ok)
        buttons.addWidget(cancel)

        layout.addLayout(buttons)

        self.nameEdit.setText(str(item.get("name", "")))
        self.qtySpin.setValue(float(item.get("qty", 1) or 1))
        self.priceSpin.setValue(float(item.get("price", 0) or 0))

        discount_type = normalize_discount_type(item.get("discount_type"))
        index = self.discountTypeCombo.findData(discount_type)
        self.discountTypeCombo.setCurrentIndex(index if index >= 0 else 0)
        self.discountValueSpin.setValue(float(item.get("discount_value", 0) or 0))
        self.update_discount_state()

    def update_discount_state(self):
        discount_type = self.discountTypeCombo.currentData()
        enabled = discount_type != DISCOUNT_NONE
        self.discountValueSpin.setEnabled(enabled)
        if discount_type == DISCOUNT_PERCENT:
            self.discountValueSpin.setMaximum(100)
            self.discountValueSpin.setSuffix(" %")
        else:
            self.discountValueSpin.setMaximum(1000000)
            self.discountValueSpin.setSuffix(" грн")
        if not enabled:
            self.discountValueSpin.setValue(0)

    def get_data(self):
        discount_type = self.discountTypeCombo.currentData()
        return {
            "name": self.nameEdit.text(),
            "qty": self.qtySpin.value(),
            "price": self.priceSpin.value(),
            "discount_type": discount_type,
            "discount_value": self.discountValueSpin.value() if discount_type != DISCOUNT_NONE else 0.0,
        }
