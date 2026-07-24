import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QAbstractItemView, QApplication, QPushButton, QStyle, QTableWidget, QWidget


STYLESHEET_TEMPLATE = """
QWidget {
    color: #172033;
    font-family: "__APP_FONT__", "Segoe UI", "Arial";
    font-size: 10pt;
}

QMainWindow,
QDialog {
    background: #f4f7fb;
}

QScrollArea {
    background: #f4f7fb;
    border: 0;
}

QFrame[role="surface"] {
    background: #ffffff;
    border: 1px solid #dce4ef;
    border-radius: 8px;
}

QLabel[variant="title"] {
    color: #0f172a;
    font-size: 18pt;
    font-weight: 700;
}

QLabel[variant="subtitle"] {
    color: #5b667a;
}

QLabel[variant="section"] {
    color: #17324d;
    font-size: 11pt;
    font-weight: 700;
}

QLabel[variant="muted"] {
    color: #64748b;
}

QLabel[variant="summary"] {
    color: #0f172a;
    font-size: 14pt;
    font-weight: 800;
}

QLineEdit,
QComboBox,
QDateEdit,
QDoubleSpinBox,
QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #cbd6e2;
    border-radius: 6px;
    min-height: 20px;
    padding: 5px 9px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QLineEdit:focus,
QComboBox:focus,
QDateEdit:focus,
QDoubleSpinBox:focus,
QPlainTextEdit:focus {
    border-color: #2563eb;
}

QLineEdit:disabled,
QComboBox:disabled,
QDateEdit:disabled,
QDoubleSpinBox:disabled,
QPlainTextEdit:disabled {
    color: #94a3b8;
    background: #eef2f7;
}

QComboBox::drop-down,
QDateEdit::drop-down,
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button {
    border: 0;
    width: 26px;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #cbd6e2;
    border-radius: 6px;
    color: #172033;
    font-weight: 650;
    min-height: 28px;
    padding: 6px 12px;
}

QPushButton:hover {
    background: #f8fafc;
    border-color: #8ea0b8;
}

QPushButton:pressed {
    background: #e7edf5;
}

QPushButton:disabled {
    color: #94a3b8;
    background: #eef2f7;
    border-color: #d7e0ea;
}

QPushButton[role="primary"] {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
}

QPushButton[role="primary"]:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}

QPushButton[role="success"] {
    background: #0f766e;
    border-color: #0f766e;
    color: #ffffff;
}

QPushButton[role="success"]:hover {
    background: #0d6a63;
    border-color: #0d6a63;
}

QPushButton[role="danger"] {
    color: #b42318;
    border-color: #f3b8b3;
    background: #fff8f7;
}

QPushButton[role="danger"]:hover {
    background: #fee4e2;
    border-color: #fda29b;
}

QPushButton[role="subtle"] {
    color: #475569;
    background: #f8fafc;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #dce4ef;
    border-radius: 8px;
    gridline-color: #edf2f7;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
}

QTableWidget::item {
    padding: 6px 8px;
}

QTableWidget::item:selected {
    background: #dbeafe;
    color: #0f172a;
}

QHeaderView::section {
    background: #edf2f7;
    border: 0;
    border-bottom: 1px solid #d0dae7;
    color: #334155;
    font-weight: 700;
    padding: 8px 10px;
}

QScrollBar:vertical,
QScrollBar:horizontal {
    background: #f1f5f9;
    border: 0;
    margin: 0;
}

QScrollBar:vertical {
    width: 12px;
}

QScrollBar:horizontal {
    height: 12px;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background: #bac6d4;
    border-radius: 6px;
    min-height: 28px;
    min-width: 28px;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {
    background: #96a5b8;
}

QScrollBar::add-line,
QScrollBar::sub-line {
    height: 0;
    width: 0;
}

QMessageBox {
    background: #f4f7fb;
}
"""


def _resource_path(*parts) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundled_path = Path(bundle_root, *parts)
        if bundled_path.exists():
            return bundled_path
    return Path(__file__).resolve().parent.parent.joinpath(*parts)


def _load_font_family() -> str:
    family = "DejaVu Sans"
    for path in (
        _resource_path("fonts", "DejaVuSans.ttf"),
        _resource_path("fonts", "DejaVuSans-Bold.ttf"),
    ):
        if not path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            family = families[0]
    return family


def apply_modern_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    font_family = _load_font_family()
    app.setFont(QFont(font_family, 10))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f4f7fb"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#172033"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET_TEMPLATE.replace("__APP_FONT__", font_family))


def set_variant(widget: QWidget, variant: str) -> None:
    widget.setProperty("variant", variant)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def set_surface(widget: QWidget) -> None:
    widget.setProperty("role", "surface")
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def set_button_role(button: QPushButton, role: str) -> None:
    button.setProperty("role", role)
    button.style().unpolish(button)
    button.style().polish(button)


def set_button_icon(button: QPushButton, pixmap: QStyle.StandardPixmap) -> None:
    button.setIcon(button.style().standardIcon(pixmap))
    button.setIconSize(QSize(18, 18))


def polish_table(table: QTableWidget) -> None:
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(34)
    table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
