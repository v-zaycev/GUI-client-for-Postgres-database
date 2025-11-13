import psycopg2
from PyQt6.QtWidgets import (QVBoxLayout, QMessageBox, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QComboBox)
from sources.base_client import PgsqlClient

class AddPatientDialog(QDialog):
    def __init__(self, db_client : PgsqlClient, old : dict = None):
        self.pgsql_client = db_client
        super().__init__()
        if old is None:
            self.addition = True
            self.setWindowTitle("Добавление пациента")
        else:
            self.addition = False
            self.setWindowTitle("Изменение пациента")
            self.id = old["id"]
        self.resize(300, 200)
        #self.setGeometry(200, 200, 300, 200)
        
        layout = QVBoxLayout()
        
        # Форма для ввода данных
        form_layout = QFormLayout()
        
        self.first_name_input = QLineEdit()
        self.first_name_input.setMaxLength(20)
        self.last_name_input = QLineEdit()
        self.last_name_input.setMaxLength(20)
        self.father_name_input = QLineEdit()
        self.father_name_input.setMaxLength(20)

        self.ward_combo = QComboBox()
        data, _ = self.pgsql_client.select(['id', 'name'], 'wards_view')
        for i in data:
            self.ward_combo.addItem(i[1])

        self.diagnosis_combo = QComboBox()
        data, _ = self.pgsql_client.select(['id', 'name'], 'diagnosis')
        for i in data:
            self.diagnosis_combo.addItem(i[1])

        if not self.addition:
            self.first_name_input.setText(old["first_name"])
            self.last_name_input.setText(old["last_name"])
            self.father_name_input.setText(old["father_name"])
            self.diagnosis_combo.setCurrentIndex(self.diagnosis_combo.findText(old["diagnosis"]))
            self.ward_combo.setCurrentIndex(self.ward_combo.findText(old["ward"]))
            self.first_name_input.setEnabled(False)
            self.last_name_input.setEnabled(False)
            self.father_name_input.setEnabled(False)
            
        

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
    
    def get_new_data(self) -> list:
        if self.addition:
            return [
                self.first_name_input.text(),
                self.last_name_input.text(),
                self.father_name_input.text(),
                self.diagnosis_combo.currentText(),
                self.ward_combo.currentText()
            ]
        else:
            return [
                self.diagnosis_combo.currentText(),
                self.ward_combo.currentText()
            ]
    
    def add_patient(self, data):
        try:
            if self.addition:
                attributes = [ 'first_name','last_name','father_name','diagnosis', 'ward']
                self.pgsql_client.insert(attributes, 'people_view', data)
            else:
                attributes = ['diagnosis', 'ward']
                self.pgsql_client.update(attributes, 'people_view', data, self.id)
        except psycopg2.Error as e:
            QMessageBox.critical(None, "Ошибка базы данных", str(e.diag.message_primary))



    
