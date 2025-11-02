import sys
import psycopg2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QMessageBox, QHBoxLayout, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QStackedWidget)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal
from login_window import LoginWidget
from main_window.main_window import MainAppWidget
from base_client import PgsqlClient
from main_window.exit_dialog import LogoutDialog

class AddWardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить новую палату")
        self.setGeometry(200, 200, 300, 200)
        layout = QVBoxLayout()
        
        # Форма для ввода данных
        form_layout = QFormLayout()
        form_layout.setContentsMargins(25, 20, 25, 20)
        self.name_input = QLineEdit()
        form_layout.addRow("Название палаты:", self.name_input)
        
        self.capacity_input = QLineEdit()
        form_layout.addRow("Вместимость:", self.capacity_input)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.base_client = PgsqlClient()
    
    def get_data(self):
        return {
            'name': self.name_input.text(),
            'max_count': self.capacity_input.text()
        }

class HospitalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pgsql_client = PgsqlClient()
        self.setWindowTitle("Hospital")

        self.setGeometry(100, 100, 800, 600)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.login_widget = LoginWidget(self.pgsql_client)
        self.stacked_widget.addWidget(self.login_widget)
        self.login_widget.login_signal.connect(self.on_login)
        self.main_app_widget = None
        
    def on_login(self, username):
        """Вызывается при успешном входе"""
        
        # Создаем основное приложение
        self.main_app_widget = MainAppWidget(self.pgsql_client)
        self.main_app_widget.logout_signal.connect(self.on_logout)
        #self.main_app_widget.logout_request.connect(self.on_logout)
        
        # Добавляем в стек (теперь индекс 1)
        self.stacked_widget.addWidget(self.main_app_widget)
        
        # Переключаемся на основное приложение
        self.stacked_widget.setCurrentIndex(1)
        
        # Меняем заголовок и размер
        self.setWindowTitle(f"Медицинская система - {username}")
        self.resize(800, 600)
        
        # Показываем меню, статус бар и т.д.
        self.setup_main_interface()

    def on_logout(self):
        dialog = LogoutDialog(self)
        dialog.exec()
        self.pgsql_client.log_out()
        self.stacked_widget.setCurrentIndex(0)

    def setup_main_interface(self):
        """Настройка интерфейса основного приложения"""
        statusbar = self.statusBar()
        statusbar.showMessage("Готово к работе")

    def get_connection(self, user : str, password : str):
        """Создает и возвращает соединение с базой данных"""
        return psycopg2.connect(
            host="localhost",
            port = 5432,
            database="hospital",
            user = user,
            password = password
        )
    
    def load_data(self, table_name : str):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Выполнение SELECT запроса
            cursor.execute("SELECT * FROM " + table_name)
            wards = cursor.fetchall()
            
            # Получаем названия колонок
            column_names = [desc[0] for desc in cursor.description]
            
            # Настраиваем таблицу
            self.table.setRowCount(len(wards))
            self.table.setColumnCount(len(column_names))
            self.table.setHorizontalHeaderLabels(column_names)
            
            # Заполняем таблицу данными
            for row_idx, ward in enumerate(wards):
                for col_idx, value in enumerate(ward):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            # Автоподбор размера колонок
            self.table.resizeColumnsToContents()
            
            # Обновляем статус
            self.status_label.setText(f"Загружено записей: {len(wards)}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
            self.status_label.setText("Ошибка при загрузке данных")
    
    def show_add_dialog(self):
        """Показывает диалог добавления новой палаты"""
        dialog = AddWardDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.add_ward_to_db(data)
    
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HospitalApp()
    window.show()
    sys.exit(app.exec())