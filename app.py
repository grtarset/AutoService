from PySide6.QtWidgets import QApplication


class AutoServiceApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self.setApplicationName("AutoService")
        self.setOrganizationName("grtarset")