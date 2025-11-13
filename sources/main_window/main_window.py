from PyQt6.QtWidgets import (QTabWidget, QWidget, QVBoxLayout, QPushButton, 
                             QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import pyqtSignal
from sources.base_client import PgsqlClient

from sources.main_window.main_table_widget import MainTableWidget
from sources.main_window.directories_widget import DirectoriesWidget
from sources.main_window.reports_widget import ReportsWidget


class MainAppWidget(QWidget):
    logout_signal = pyqtSignal()
    
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        self.tabs = QTabWidget()
        self.mainTable = MainTableWidget(db_client)
        self.directories = DirectoriesWidget(db_client)
        self.reports = ReportsWidget(db_client)
        self.tabs.addTab(self.mainTable, "Журнал")
        self.tabs.addTab(self.directories, "Справочники")
        self.tabs.addTab(self.reports, "Отчёты")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)  
        
        self.setLayout(layout)
        self.tabs.setCurrentIndex(0)

        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.logout_btn = QPushButton("Выход", self)
        self.logout_btn.clicked.connect(self.logout_signal.emit)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffcccc;
                color: #990000;
                border: 1px solid #ff9999;
                border-radius: 10px;    /* Чуть меньше радиус для маленькой кнопки */
                padding: 6px 12px;      /* Уменьшенные отступы */
                font-size: 12px;        /* Чуть меньший шрифт */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffb3b3;
                border: 1px solid #ff6666;
            }
            QPushButton:pressed {
                background-color: #ff9999;
            }
        """)

    def resizeEvent(self, event):
        self.logout_btn.move(self.width() - 130, 45)
        super().resizeEvent(event)        

    def create_navigation(self):
        # Панель с кнопками для переключения
        nav_layout = QHBoxLayout()
        
        self.btn_main = QPushButton("Основная таблица")
        self.btn_dirs = QPushButton("Справочники")
        self.btn_reports = QPushButton("Отчеты")
        
        nav_layout.addWidget(self.btn_main)
        nav_layout.addWidget(self.btn_dirs)
        nav_layout.addWidget(self.btn_reports)
        
        # Подключаем переключение
        self.btn_main.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.btn_dirs.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.btn_reports.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        
        return nav_layout
    