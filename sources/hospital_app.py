from PyQt6.QtWidgets import (QMainWindow, QStackedWidget)
from sources.login_window import LoginWidget
from sources.main_window.main_window import MainAppWidget
from sources.base_client import PgsqlClient
from sources.main_window.exit_dialog import LogoutDialog

class HospitalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pgsql_client = PgsqlClient()
        self.setWindowTitle("Hospital")
        self.resize(800, 600)
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.login_widget = LoginWidget(self.pgsql_client)
        self.stacked_widget.addWidget(self.login_widget)
        self.login_widget.login_signal.connect(self.on_login)
        self.main_app_widget = None
        
    def on_login(self, username):        
        self.main_app_widget = MainAppWidget(self.pgsql_client)
        self.main_app_widget.logout_signal.connect(self.on_logout)
        
        self.stacked_widget.addWidget(self.main_app_widget)
        self.stacked_widget.setCurrentIndex(1)
        
        self.setWindowTitle(f"Hospital - {username}")
        self.resize(800, 600)
        
    def on_logout(self):
        dialog = LogoutDialog(self)
        dialog.switch_user_clicked.connect(self.logout)
        dialog.logout_clicked.connect(self.exit)
        dialog.exec()

    def logout(self):
        self.pgsql_client.log_out()
        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.removeWidget(self.main_app_widget)
        self.main_app_widget = None
        self.setWindowTitle("Hospital")

    def exit(self):
        self.pgsql_client.log_out()
        self.close()
    