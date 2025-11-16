import psycopg2
from PyQt6.QtWidgets import (QVBoxLayout, QMessageBox, QLineEdit,
                             QFormLayout, QDialog, QDialogButtonBox,
                             QComboBox, QSpinBox)
from sources.base_client import PgsqlClient

class AddWardDialog(QDialog):
    def __init__(self, db_client : PgsqlClient, old : dict = None):
        self.pgsql_client = db_client
        super().__init__()
        if old is None:
            self.addition = True
            self.setWindowTitle("Добавление палаты")
        else:
            self.addition = False
            self.setWindowTitle("Изменение палаты")
            self.id = old["id"]
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.ward_name_input = QLineEdit()
        self.ward_name_input.setMaxLength(20)
        self.ward_size_input = QSpinBox()
        self.ward_size_input.setRange(1, 20)
        self.ward_size_input.setValue(1)
        self.ward_size_input.setSingleStep(1)

        self.diagnosis_combo = QComboBox()
        data, _ = self.pgsql_client.select(['id', 'name'], 'diagnosis')
        for i in data:
            self.diagnosis_combo.addItem(i[1])

        if not self.addition:
            self.ward_name_input.setText(old["name"])
            self.ward_size_input.setValue(int(old['max_count']))
            self.diagnosis_combo.setCurrentIndex(self.diagnosis_combo.findText(old["diagnosis"]))

        form_layout.addRow("Название:", self.ward_name_input)        
        form_layout.addRow("Вместимость:", self.ward_size_input)
        form_layout.addRow("Диагноз:", self.diagnosis_combo)

        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_new_data(self) -> list:
        return [
            self.ward_name_input.text(),
            self.ward_size_input.value(),
            self.diagnosis_combo.currentText()
        ]
    
    def add_patient(self, data):
        try:
            if self.addition:
                attributes = [ 'name', 'max_count', 'diagnosis']
                self.pgsql_client.insert(attributes, 'wards_view', data)
            else:
                attributes = [ 'name', 'max_count', 'diagnosis']
                self.pgsql_client.update(attributes, 'wards_view', data, self.id)
        except psycopg2.Error as e:
            QMessageBox.critical(None, "Ошибка базы данных", str(e.diag.message_primary))



    
