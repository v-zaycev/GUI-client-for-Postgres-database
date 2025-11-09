import sys
from PyQt6.QtWidgets import QApplication
from sources.hospital_app import HospitalApp

def main():
    app = QApplication(sys.argv)
    window = HospitalApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()