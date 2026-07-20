import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


def resource_path(*parts) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundled_path = Path(bundle_root, *parts)
        if bundled_path.exists():
            return bundled_path
    return Path(__file__).resolve().parent.joinpath(*parts)


def app_icon() -> QIcon:
    icon_path = resource_path("assets", "logo.png")
    return QIcon(str(icon_path))


class AutoServiceApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self.setApplicationName("AutoService")
        self.setOrganizationName("grtarset")
        self.setWindowIcon(app_icon())
