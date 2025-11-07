from PyQt6.QtWidgets import (QTabWidget, QHeaderView, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QMessageBox, QHBoxLayout, QSizePolicy,
                             QToolButton, QMenu, QTableView)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal, Qt, QAbstractTableModel
from PyQt6.QtPrintSupport import QPrinter
from base_client import PgsqlClient
from main_window.basic_widget import BasicWidget
from main_window.patient_edit_dialog import AddPatientDialog
from main_window.ward_edit_dialog import AddWardDialog
from main_window.diagnosis_edit_dialog import AddDiagnosisDialog
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
import os

from main_window.names_conversion import names_conversion
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

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

class MainTableWidget(BasicWidget):
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        # Создаем layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Заголовок
        title_label = QLabel("Текущие пациенты")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px;")
        layout.addWidget(title_label)
        
        # Панель кнопок
        self.buttons_layout = self.init_buttons()
        self.layout().addLayout(self.buttons_layout)
        
        # Таблица для отображения данных
        self.table = self.init_table()
        self.table.itemSelectionChanged.connect(lambda: self.update_buttons_states(len(self.table.selectionModel().selectedRows())))
        layout.addWidget(self.table)

        
        # Статус
        self.status_label = QLabel("Нажмите кнопку для загрузки данных")
        layout.addWidget(self.status_label)
        
        # Загружаем данные при старте
        self.current_table_name = "people_view"
        self.rights = {"people_view" : self.pgsql_client.get_table_rights("people_view")}
        data, description = self.pgsql_client.select(['*'], 'people_view')
        self.set_buttons_states()
        self.load_button.clicked.connect(self.load_data)
        self.update_button.clicked.connect(lambda: self.show_add_dialog(self.get_selected_rows_data(self.table)))
        self.insert_button.clicked.connect(lambda: self.show_add_dialog())
        self.delete_button.clicked.connect(self.delete_rows)
        self.show_data(data, description)

    def show_add_dialog(self, old : list[list[str]] = None):
        if old is None or len(old) == 0:
            data = None
        else:
            data = {
                "id" : old[0][0],
                "first_name" : old[0][1],
                "last_name" : old[0][2],
                "father_name" : old[0][3],
                "diagnosis" : old[0][4],
                "ward" : old[0][5]
            }
        dialog = AddPatientDialog(self.pgsql_client, data)
        if dialog.exec():
            data = dialog.get_new_data()
            dialog.add_patient(data)
        data, description = self.pgsql_client.select(['*'], 'people_view')
        self.table.clearSelection()
        self.show_data(data, description)

class DirectoriesWidget(BasicWidget):
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Заголовок
        title_label = QLabel("Данные из таблицы people")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        

        # Панель кнопок
        self.buttons_layout = self.init_buttons()
        self.layout().addLayout(self.buttons_layout)
        self.load_button.clicked.connect(self.load_data)
        self.update_button.clicked.connect(lambda: self.show_add_dialog(self.get_selected_rows_data(self.table)))
        self.insert_button.clicked.connect(lambda: self.show_add_dialog())
        self.delete_button.clicked.connect(self.delete_rows)

        self.tool_btn = QToolButton()
        self.tool_btn.setText("Справочники")  # Текст кнопки
        self.tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        # Создаем выпадающее меню
        self.dropdown_menu = QMenu()
        action1 = QAction("Палаты", self)
        action2 = QAction("Диагнозы", self)
        self.dropdown_menu.addAction(action1)
        self.dropdown_menu.addAction(action2)

        # Привязываем меню к кнопке
        self.tool_btn.setMenu(self.dropdown_menu)

        # Подключаем обработчики
        action1.triggered.connect(lambda: self.set_table("wards_view"))
        action2.triggered.connect(lambda: self.set_table("diagnosis"))
        layout.addWidget(self.tool_btn)

        # Таблица для отображения данных
        self.table = self.init_table()
        self.table.itemSelectionChanged.connect(lambda: self.update_buttons_states(len(self.table.selectionModel().selectedRows())))
        layout.addWidget(self.table)

        # Статус
        self.status_label = QLabel("Нажмите кнопку для загрузки данных")
        layout.addWidget(self.status_label)

        self.rights = {"wards_view" : self.pgsql_client.get_table_rights("wards_view"),
                       "diagnosis" : self.pgsql_client.get_table_rights("wards_view")}
        self.set_table("wards_view")

    def set_table(self, table : str):
        self.current_table_name = table
        self.set_buttons_states()
        data, description = self.pgsql_client.select(["*"], table)
        self.show_data(data, description)
    
    def show_add_dialog(self, old : list[list[str]] = None):
        if old is None or len(old) == 0:
            data = None
        else:
            if self.current_table_name == 'wards_view':
                data = {
                    "id" : old[0][0],
                    "name" : old[0][1],
                    "max_count" : old[0][2],
                    "diagnosis" : old[0][3]
                }
            elif self.current_table_name == 'diagnosis':
                data = {
                    "id" : old[0][0],
                    "name" : old[0][1],
                }
        if self.current_table_name == 'wards_view':
            dialog = AddWardDialog(self.pgsql_client, data)
        elif self.current_table_name == 'diagnosis':
            dialog = AddDiagnosisDialog(self.pgsql_client, data)
        if dialog.exec():
            data = dialog.get_new_data()
            dialog.add_patient(data)
        data, description = self.pgsql_client.select(['*'], self.current_table_name)
        self.table.clearSelection()
        self.show_data(data, description)

class ReportsWidget(BasicWidget):
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Заголовок
        title_label = QLabel("Данные из таблицы people")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Панель кнопок
        self.buttons_layout = self.init_buttons()
        self.layout().addLayout(self.buttons_layout)
        self.load_button.clicked.connect(self.load_data)
        self.export_xlsx.clicked.connect(self.create_xlsx_report)
        self.export_csv.clicked.connect(self.create_csv_report)
        self.export_pdf.clicked.connect(self.export_to_pdf)

        self.tool_btn = QToolButton()
        self.tool_btn.setText("Выбор отчёта")  # Текст кнопки
        self.tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        # Создаем выпадающее меню
        self.dropdown_menu = QMenu()
        action1 = QAction("Статистика по палатам", self)
        action2 = QAction("Статистика по болезням", self)
        self.dropdown_menu.addAction(action1)
        self.dropdown_menu.addAction(action2)

        # Привязываем меню к кнопке
        self.tool_btn.setMenu(self.dropdown_menu)

        # Подключаем обработчики
        action1.triggered.connect(lambda: self.set_table("ward_occupancy_report"))
        action2.triggered.connect(lambda: self.set_table("diagnosis_statistics"))
        layout.addWidget(self.tool_btn)

        # Таблица для отображения данных
        self.table = self.init_table()
        layout.addWidget(self.table)

        # Статус
        self.status_label = QLabel("Нажмите кнопку для загрузки данных")
        layout.addWidget(self.status_label)

        self.rights = {"ward_occupancy_report" : self.pgsql_client.get_table_rights("ward_occupancy_report"),
                       "diagnosis_statistics" : self.pgsql_client.get_table_rights("diagnosis_statistics")}
        self.set_table("ward_occupancy_report")

    def set_table(self, table : str):
        self.current_table_name = table
        self.data, self.description = self.pgsql_client.select(["*"], table)
        self.show_data(self.data, self.description)
        self.create_xlsx_report()
    
    def create_xlsx_report(self):
        df = pd.DataFrame(data = self.data, columns=[names_conversion[self.current_table_name][desc[0]] for desc in self.description])
        self.save_df_with_auto_width(df,"report.xlsx")

    def create_csv_report(self):
        df = pd.DataFrame(data = self.data, columns=[names_conversion[self.current_table_name][desc[0]] for desc in self.description])
        df.to_csv("report.csv", index = False)

    def init_buttons(self) -> QHBoxLayout:
        buttons_layout = QHBoxLayout()

        self.load_button = QPushButton("Обновить данные")
        self.load_button.setEnabled(True)
        self.load_button.setFixedWidth(120)
        buttons_layout.addWidget(self.load_button)
        
        # Кнопки
        self.export_xlsx = QPushButton("Экспортировать в .xlsx")
        self.export_csv = QPushButton("Экспортировать в .csv") 
        self.export_pdf = QPushButton("Экспортировать в .pdf")
        
        self.export_xlsx.setEnabled(True)
        self.export_csv.setEnabled(True)
        self.export_pdf.setEnabled(True)
        
        # Фиксируем ширину для аккуратного вида
        self.export_xlsx.setFixedWidth(150)
        self.export_csv.setFixedWidth(150)
        self.export_pdf.setFixedWidth(150)
        
        buttons_layout.addWidget(self.export_xlsx)
        buttons_layout.addWidget(self.export_csv)
        buttons_layout.addWidget(self.export_pdf)
        buttons_layout.addStretch()
                
        return buttons_layout
    
    def save_df_with_auto_width(self, df : pd.DataFrame, filename):
        df.to_excel(filename, index=False, engine='openpyxl')
        
        workbook = load_workbook(filename)
        worksheet = workbook.active
        
        # Автоматическая ширина для каждого столбца
        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    # Учитываем длину текста в ячейке
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # максимум 50 символов
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        workbook.save(filename)

    def export_to_pdf(self):

        try:
            # Попробуем найти стандартные шрифты Windows
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/times.ttf", 
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf"  # для Linux
            ]
            
            font_registered = False
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('CyrillicFont', font_path))
                    font_registered = True
                    break
                    
            if not font_registered:
                # Используем стандартный шрифт ReportLab (ограниченная поддержка кириллицы)
                pdfmetrics.registerFont(TTFont('CyrillicFont', 'Helvetica'))
        except:
            pdfmetrics.registerFont(TTFont('CyrillicFont', 'Helvetica'))



        doc = SimpleDocTemplate(self.current_table_name + '.pdf', pagesize=landscape(A4))
        elements = []
        
        df = pd.DataFrame(data = self.data, columns=[names_conversion[self.current_table_name][desc[0]] for desc in self.description])
        data = [df.columns.tolist()] + df.values.tolist()
        
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.fontName = 'CyrillicFont'
    
        # Добавляем титульную надпись
        title_paragraph = Paragraph("Отчёт", title_style)
        elements.append(title_paragraph)
        elements.append(Spacer(1, 20))  # отступ после заголовка

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'CyrillicFont'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        