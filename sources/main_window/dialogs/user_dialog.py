import psycopg2
from PyQt6.QtWidgets import (QVBoxLayout, QMessageBox, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QComboBox, QCheckBox)
from sources.base_client import PgsqlClient
from PyQt6.QtCore import Qt 
class AddUserDialog(QDialog):
    def __init__(self, db_client : PgsqlClient, old : dict = None):
        self.pgsql_client = db_client
        super().__init__()
        if old is None:
            self.id = None
            self.setWindowTitle("Добавление пользователя")
        else:
            self.setWindowTitle("Изменение пользователя")
            self.id = old["id"]
        self.resize(300, 160)
        
        layout = QVBoxLayout()
        
        # Форма для ввода данных
        form_layout = QFormLayout()

        self.login = QLineEdit()
        self.login.setMaxLength(50)
        self.password = QLineEdit()
        self.password.setMaxLength(30)
        self.password.setEnabled(True)
        self.role_combo = QComboBox()
        data, _ = self.pgsql_client.select(['*'], 'roles_table')
        for i in data:
            if i[0] != 'super_user':
                 self.role_combo.addItem(i[0])


        form_layout.addRow("Логин:", self.login)        
        form_layout.addRow("Пароль:", self.password)
        form_layout.addRow("Роль:", self.role_combo)
        if self.id is not None:
            self.login.setText(old["username"])
            self.role_combo.setCurrentIndex(self.role_combo.findText(old["user_role"]))
            self.login.setEnabled(True)
            self.password.setEnabled(False)
            self.role_combo.setEnabled(True)
            self.pass_checkbox = QCheckBox("Не изменять пароль")
            self.pass_checkbox.setCheckState(Qt.CheckState.Checked)
            self.pass_checkbox.stateChanged.connect(self.reset_pass)
            form_layout.addRow("       ", self.pass_checkbox)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_new_data(self) -> list:
        return [
            self.login.text(),
            self.password.text(),
            self.role_combo.currentText()
        ]
    
    def edit_user(self, data):
        try:
            attributes = ['username','password_hash','user_role']
            self.pgsql_client.edit_user(attributes, data, self.id)
        except psycopg2.Error as e:
            QMessageBox.critical(None, "Ошибка базы данных", str(e.diag.message_primary))


    def reset_pass(self, state):
        if state == Qt.CheckState.Checked.value:
            self.password.setText("")
            self.password.setEnabled(False)
        else:
            self.password.setEnabled(True)
