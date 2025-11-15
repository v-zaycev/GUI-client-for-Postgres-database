import psycopg2
from PyQt6.QtWidgets import (QVBoxLayout, QMessageBox, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QComboBox)
from sources.base_client import PgsqlClient

class AddUserDialog(QDialog):
    def __init__(self, db_client : PgsqlClient, old : dict = None):
        self.pgsql_client = db_client
        super().__init__()
        if old is None:
            self.addition = True
            self.setWindowTitle("Добавление пользователя")
        else:
            self.addition = False
            self.setWindowTitle("Изменение пользователя")
            self.id = old["id"]
        self.resize(300, 200)
        #self.setGeometry(200, 200, 300, 200)
        
        layout = QVBoxLayout()
        
        # Форма для ввода данных
        form_layout = QFormLayout()
        
        self.login = QLineEdit()
        self.login.setMaxLength(50)
        self.password = QLineEdit()
        self.password.setMaxLength(30)

        self.role_combo = QComboBox()
        data, _ = self.pgsql_client.select(['id', 'user_role'], 'users', "user_role != 'super_role'")
        for i in data:
            if i[1] != 'super_user':
                 self.role_combo.addItem(i[1])


        if not self.addition:
            self.login.setText(old["username"])
            self.password.setText(old["password_hash"])
            self.role_combo.setCurrentIndex(self.role_combo.findText(old["user_role"]))
            self.login.setEnabled(False)
            self.password.setEnabled(True)
            self.role_combo.setEnabled(False)
            
        

        form_layout.addRow("Логин:", self.login)        
        form_layout.addRow("Пароль:", self.password)
        form_layout.addRow("Роль:", self.role_combo)

        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_new_data(self) -> list:
        if self.addition:
            return [
                self.login.text(),
                self.password.text(),
                self.role_combo.currentText()
            ]
        else:
            return [
                self.password.currentText(),
                self.role_combo.currentText()
            ]
    
    def add_user(self, data):
        try:
            if self.addition:
                attributes = [ 'username','password_hash','user_role']
                self.pgsql_client.insert_user(attributes, data[0], data[1], data[2])
            else:
                attributes = [ 'username','password_hash','user_role']
                self.pgsql_client.update_user(attributes, data, self.id)
        except psycopg2.Error as e:
            QMessageBox.critical(None, "Ошибка базы данных", str(e.diag.message_primary))
