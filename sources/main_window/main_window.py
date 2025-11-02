import psycopg2
from PyQt6.QtWidgets import (QTabWidget, QHeaderView, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QMessageBox, QHBoxLayout, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QSizePolicy, QToolButton, QMenu, QComboBox)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal
from base_client import PgsqlClient


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

class MainTableWidget(QWidget):
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        # Создаем layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Заголовок
        title_label = QLabel("Данные из таблицы people")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        

        # Панель кнопок
        self.buttons_layout = init_buttons(self)
        #self.update_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        
        # Таблица для отображения данных
        self.table = setup_table()
        layout.addWidget(self.table)

        
        # Статус
        self.status_label = QLabel("Нажмите кнопку для загрузки данных")
        layout.addWidget(self.status_label)
#        central_widget.setLayout(layout)
        
        conn = self.get_connection("postgres", "159753")
        cursor = conn.cursor()
        
        # Выполнение SELECT запроса
        cursor.execute("SELECT * FROM people_explicit")
        data = cursor.fetchall()
        description = cursor.description
        cursor.close()
        conn.close()
        # Загружаем данные при старте

        rights = self.pgsql_client.get_table_rights("people_explicit")
        set_buttons_rights(self, rights)
        self.show_data(data, description)
        
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

    def get_connection(self, user : str, password : str):
        """Создает и возвращает соединение с базой данных"""
        return psycopg2.connect(
            host="localhost",
            port = 5432,
            database="hospital",
            user = user,
            password = password
        )

    def show_add_dialog(self):
        dialog = AddWardDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.add_ward_to_db(data)

class DirectoriesWidget(QWidget):
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
        self.buttons_layout = init_buttons(self)

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
        action1.triggered.connect(lambda: self.get_data("wards"))
        action2.triggered.connect(lambda: self.get_data("diagnosis"))
        layout.addWidget(self.tool_btn)

        # Таблица для отображения данных
        self.table = setup_table()
        layout.addWidget(self.table)

        # Статус
        self.status_label = QLabel("Нажмите кнопку для загрузки данных")
        layout.addWidget(self.status_label)

        rights = self.pgsql_client.get_table_rights("wards")
        set_buttons_rights(self, rights)
        self.get_data("wards")
    
    def get_data(self, table : str):
        conn = self.get_connection("postgres", "159753")
        cursor = conn.cursor()
        
        # Выполнение SELECT запроса
        cursor.execute("SELECT * FROM " + table)
        data = cursor.fetchall()
        description = cursor.description
        cursor.close()
        conn.close()
        # Загружаем данные при старте
        self.show_data(data, description)

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

    def get_connection(self, user : str, password : str):
        """Создает и возвращает соединение с базой данных"""
        return psycopg2.connect(
            host="localhost",
            port = 5432,
            database="hospital",
            user = user,
            password = password
        )

class ReportsWidget(QWidget):
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

class AddWardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление пациента")
        self.setGeometry(200, 200, 300, 200)
        
        layout = QVBoxLayout()
        
        # Форма для ввода данных
        form_layout = QFormLayout()
        
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.father_name_input = QLineEdit()
        
        self.ward_combo = QComboBox()
        data = self.get_data("SELECT id, name, diagnosis_id FROM wards")
        wards_map = {}
        for i in data:
            wards_map[i[1]] = (i[0], i[2])
            self.ward_combo.addItem(i[1])

        self.diagnosis_combo = QComboBox()
        data = self.get_data("SELECT id, name FROM diagnosis")
        diagnosis_map = {}
        for i in data:
            diagnosis_map[i[1]] = i[0]
            self.diagnosis_combo.addItem(i[1])


   #     self.diagnosis_combo = QComboBox()

        form_layout.addRow("Имя:", self.first_name_input)        
        form_layout.addRow("Фамилия:", self.last_name_input)
        form_layout.addRow("Отчетство:", self.father_name_input)
        form_layout.addRow("Диагноз:", self.diagnosis_combo)
        form_layout.addRow("Палата:", self.ward_combo)

        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_new_data(self):
        return {
            'first_name': self.first_name_input.text(),
            'last_name': self.last_name_input.text(),
            'father_name': self.father_name_input.text(),
            'ward_id': self.ward_combo.currentData()
        }
    def add_ward_to_db(self, data):
        """Добавляет новую палату в базу данных"""
        try:
            # Проверяем обязательные поля
            if not data['name'] or not data['max_count']:
                QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
                return
            
            # Проверяем, что вместимость - число
            try:
                capacity = int(data['max_count'])
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Вместимость должна быть числом!")
                return
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Выполняем INSERT запрос
            cursor.execute(
                "INSERT INTO wards (name, max_count) VALUES (%s, %s)",
                (data['name'], capacity)
            )
            
            # Подтверждаем изменения
            conn.commit()
            
            # Обновляем таблицу
            self.load_wards_data()
            
            QMessageBox.information(self, "Успех", "Палата успешно добавлена!")
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Ошибка при добавлении:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка:\n{str(e)}")

    def get_data(self, request : str):
        conn = self.get_connection("postgres", "159753")
        cursor = conn.cursor()
        
        cursor.execute(request)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data
    
    def get_connection(self, user : str, password : str):
        """Создает и возвращает соединение с базой данных"""
        return psycopg2.connect(
            host="localhost",
            port = 5432,
            database="hospital",
            user = user,
            password = password
        )
    

def setup_table() -> QTableWidget:
    table = QTableWidget()
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    horizontal_header = table.horizontalHeader()
    vertical_header = table.verticalHeader()
    horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    return table


def init_buttons(widget : QWidget) -> QHBoxLayout:
    #can_insert, can_update, can_delete = cursor.fetchone()
    
    # Вертикальный layout
    buttons_layout = QHBoxLayout()
#    buttons_layout.setSpacing(5)

    widget.load_button = QPushButton("Обновить данные")
    widget.load_button.setEnabled(True)
    widget.load_button.setFixedWidth(120)
    buttons_layout.addWidget(widget.load_button)
    
    # Кнопки
    widget.insert_button = QPushButton("Добавить запись")
    widget.update_button = QPushButton("Изменить запись") 
    widget.delete_button = QPushButton("Удалить записи")
    
    widget.insert_button.setEnabled(False)
    widget.update_button.setEnabled(False)
    widget.delete_button.setEnabled(False)
    widget.insert_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
    widget.update_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
    widget.delete_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
    
    # Фиксируем ширину для аккуратного вида
    widget.insert_button.setFixedWidth(120)
    widget.update_button.setFixedWidth(120)
    widget.delete_button.setFixedWidth(120)
    
    buttons_layout.addWidget(widget.insert_button)
    buttons_layout.addWidget(widget.update_button)
    buttons_layout.addWidget(widget.delete_button)
    buttons_layout.addStretch()
    
    widget.layout().addLayout(buttons_layout)
    
    return buttons_layout

def set_buttons_rights(widget : QWidget, rights : list ):
    if len(rights) != 1:
        return
    if rights[0][2]:
        widget.insert_button.setStyleSheet("QPushButton {}")
        widget.insert_button.setEnabled(True)
    if rights[0][3]:
        widget.update_button.setStyleSheet("QPushButton {}")
        widget.update_button.setEnabled(True)
    if rights[0][4]:
        widget.delete_button.setStyleSheet("QPushButton {}")
        widget.delete_button.setEnabled(True)
