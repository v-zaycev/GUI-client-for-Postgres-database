from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class LogoutDialog(QDialog):
    logout_clicked = pyqtSignal()
    switch_user_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Завершение работы")
        self.setFixedSize(220, 140)  # Уменьшил высоту окна
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(6)  # Уменьшил расстояние между кнопками
        layout.setContentsMargins(20, 15, 20, 15)  # Уменьшил отступы
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Кнопки в столбик
        self.btn_switch = QPushButton("Сменить пользователя")
        self.btn_logout = QPushButton("Выход")
        self.btn_cancel = QPushButton("Отмена")
        
        self.btn_switch.setFixedHeight(28)
        self.btn_switch.setFixedWidth(150)
        self.btn_logout.setFixedHeight(28)
        self.btn_logout.setFixedWidth(150)
        self.btn_cancel.setFixedHeight(28)
        self.btn_cancel.setFixedWidth(150)
        
        # Подключаем сигналы
        self.btn_switch.clicked.connect(self.on_switch_user)
        self.btn_logout.clicked.connect(self.on_logout)
        self.btn_cancel.clicked.connect(self.reject)
        
        # Добавляем кнопки в layout с центрированием
        layout.addWidget(self.btn_switch, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_logout, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
    
    def on_logout(self):
        self.logout_clicked.emit()
        self.accept()
    
    def on_switch_user(self):
        self.switch_user_clicked.emit()
        self.accept()