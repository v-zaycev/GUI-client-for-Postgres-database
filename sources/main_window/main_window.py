import psycopg2
from PyQt6.QtWidgets import (QTabWidget, QHeaderView, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QMessageBox, QHBoxLayout, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QSizePolicy, QToolButton, QMenu, QComboBox)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal, Qt
from base_client import PgsqlClient
from main_window.patient_edit_dialog import AddPatientDialog
from main_window.ward_edit_dialog import AddWardDialog
from main_window.diagnosis_edit_dialog import AddDiagnosisDialog
from main_window.names_conversion import names_conversion


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
        # Позиционируем кнопку в правом верхнем углу MainAppWidget
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

class BasicWidget(QWidget):
    pgsql_client = None
    rights = None
    current_table_name = None
    table = None

    @staticmethod
    def init_table() -> QTableWidget:
        table = QTableWidget()
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        horizontal_header = table.horizontalHeader()
        vertical_header = table.verticalHeader()
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def init_buttons(self) -> QHBoxLayout:
        buttons_layout = QHBoxLayout()

        self.load_button = QPushButton("Обновить данные")
        self.load_button.setEnabled(True)
        self.load_button.setFixedWidth(120)
        buttons_layout.addWidget(self.load_button)
        
        # Кнопки
        self.insert_button = QPushButton("Добавить запись")
        self.update_button = QPushButton("Изменить запись") 
        self.delete_button = QPushButton("Удалить записи")
        
        self.insert_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.insert_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        self.update_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        self.delete_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        
        # Фиксируем ширину для аккуратного вида
        self.insert_button.setFixedWidth(120)
        self.update_button.setFixedWidth(120)
        self.delete_button.setFixedWidth(120)
        
        buttons_layout.addWidget(self.insert_button)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        
     #   self.layout().addLayout(buttons_layout)
        
        return buttons_layout

    def set_buttons_states(self):
        if self.rights[self.current_table_name]["insert"]:
            self.insert_button.setStyleSheet("QPushButton {}")
            self.insert_button.setEnabled(True)
        if self.rights[self.current_table_name]["update"]:
            self.update_button.setStyleSheet("QPushButton {}")
            self.update_button.setEnabled(False)
        if self.rights[self.current_table_name]["delete"]:
            self.delete_button.setStyleSheet("QPushButton {}")
            self.delete_button.setEnabled(False)

    def update_buttons_states(self, selected_count : int):
        if selected_count == 1:
            if self.rights[self.current_table_name]["update"]:
                self.update_button.setEnabled(True)
            if self.rights[self.current_table_name]["delete"]:
                self.delete_button.setEnabled(True)
        elif selected_count > 1:
            self.update_button.setEnabled(False)
            if self.rights[self.current_table_name]["delete"]:
                self.delete_button.setEnabled(True)
        else:
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    @staticmethod    
    def get_column_values_from_selected(table : QTableWidget, column : int = 0) -> list[str]:
        return [table.item(row.row(), column).text() 
                for row in table.selectionModel().selectedRows()
                if table.item(row.row(), column) is not None]

    @staticmethod
    def get_selected_rows_data(table : QTableWidget) -> list[list[str]]:
        selected_data = []
        selected_indexes = table.selectionModel().selectedRows()

        for index in selected_indexes:
            row = index.row()
            row_data = []

            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
        
            selected_data.append(row_data)
        
        return selected_data

    def delete_rows(self):
        ids = self.get_column_values_from_selected(self.table)
        self.pgsql_client.delete(ids, self.current_table_name)
        data, description = self.pgsql_client.select(['*'], self.current_table_name)
        self.table.clearSelection()
        self.show_data(data, description)
    
    def show_data(self, data, description):
        try:
            # Настраиваем таблицу
            column_names = [names_conversion[self.current_table_name][desc[0]] for desc in description]
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(column_names))
            self.table.setHorizontalHeaderLabels(column_names)
            
            # Заполняем таблицу данными
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value) if value is not None else ""))
            
            # Автоподбор размера колонок
            self.table.resizeColumnsToContents()
            
            # Обновляем статус
            self.status_label.setText(f"Загружено записей: {len(data)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
            self.status_label.setText("Ошибка при загрузке данных")

    def load_data(self):
        data, description = self.pgsql_client.select(['*'], self.current_table_name)
        self.show_data(data, description)

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

    def show_data(self, data, description):
        try:
            # Настраиваем таблицу
            column_names = [desc[0] for desc in description]
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(column_names))
            self.table.setHorizontalHeaderLabels(column_names)
            
            # Заполняем таблицу данными
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            # Автоподбор размера колонок
            self.table.resizeColumnsToContents()
            
            # Обновляем статус
            self.status_label.setText(f"Загружено записей: {len(data)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
            self.status_label.setText("Ошибка при загрузке данных")
