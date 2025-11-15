from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal, Qt

from sources.base_client import PgsqlClient

class LoginWidget(QWidget):
    exit_signal = pyqtSignal()
    login_signal = pyqtSignal(str)  # передаем имя пользователя
    
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.setup_ui()
        self.pgsql_client = db_client

    def setup_ui(self):
        # Основной виджет для центрирования
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Контейнер для формы логина
        form_container = QFrame()
        form_container.setFixedSize(300, 300)
        form_layout = QVBoxLayout(form_container)
        
        # Поля ввода
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")
        self.username_input.setMaximumSize(250, 30)
        self.username_input.setMaxLength(50)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaximumSize(250, 30)
        self.password_input.setMaxLength(50)
        
        self.error_widget = QLabel("Неверный логин или пароль")
        self.error_widget.setStyleSheet("""
            QLabel {
                background-color: #ffebee;
                color: #c62828;
                padding: 8px 12px;
                border: 1px solid #ef9a9a;
                border-radius: 6px;
                font-size: 13px;
                margin: 5px 0px;
            }
        """)
        self.error_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_widget.hide()

        # Кнопка входа
        self.login_button = QPushButton("Войти")
        self.login_button.setFixedSize(120, 35)
        self.login_button.clicked.connect(self.attempt_login)
        
        # Кнопка выхода (такая же, но красная)
        self.logout_button = QPushButton("Выйти")
        self.logout_button.setFixedSize(120, 35)
        self.logout_button.clicked.connect(self.exit)  # или ваш метод выхода
        
        # Контейнер для кнопок (расположение рядом)
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)  # Расстояние между кнопками
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.logout_button)
        
        # Добавляем виджеты в форму
        form_layout.addWidget(QLabel("Логин:"))
        form_layout.addWidget(self.username_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(QLabel("Пароль:"))
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(15)
        form_layout.addWidget(self.error_widget)
        form_layout.addSpacing(15)
        form_layout.addWidget(buttons_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Добавляем форму в центрирующий layout
        form_layout.setContentsMargins(25, 20, 25, 20)
        central_layout.addWidget(form_container)
        

        # Устанавливаем центральный виджет как основной
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(central_widget)
    
    def attempt_login(self):
        try:
            username = self.username_input.text()
            password = self.password_input.text()
            
            if self.pgsql_client.log_in(username, password):
                self.error_widget.hide()
                self.username_input.clear()
                self.password_input.clear()
                self.login_signal.emit(username)
            else:
                self.error_widget.setText("Неверный логин или пароль")
                self.error_widget.show()
        except Exception as e:
            self.error_widget.setText("Не удалось подключиться к базе")
            self.error_widget.show()
    def exit(self):
        self.exit_signal.emit()
        pass
