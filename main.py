import sys

from app import AutoServiceApp
from ui.main_window import MainWindow


def main():
    app = AutoServiceApp(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
