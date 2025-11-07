import psycopg2
from PyQt6.QtWidgets import (QVBoxLayout, QMessageBox, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox)
from base_client import PgsqlClient

class AddDiagnosisDialog(QDialog):
    def __init__(self, db_client : PgsqlClient, old : dict = None):
        self.pgsql_client = db_client
        super().__init__()
        if old is None:
            self.addition = True
            self.setWindowTitle("Добавление диагноза")
        else:
            self.addition = False
            self.setWindowTitle("Изменение диагноза")
            self.id = old["id"]
        self.resize(300, 100)
        #self.setGeometry(200, 200, 300, 100)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.diagnosis_input = QLineEdit()
        self.diagnosis_input.setMaxLength(20)

        if not self.addition:
            self.diagnosis_input.setText(old["name"])

        form_layout.addRow("Диагноз:", self.diagnosis_input)

        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_new_data(self) -> list:
        return [self.diagnosis_input.text()]
    
    def add_patient(self, data):
        try:
            if self.addition:
                attributes = [ 'name']
                self.pgsql_client.insert(attributes, 'diagnosis', data)
            else:
                attributes = [ 'name']
                self.pgsql_client.update(attributes, 'diagnosis', data, self.id)
        except psycopg2.Error as e:
            QMessageBox.critical(None, "Ошибка базы данных", str(e.diag.message_primary))



    
