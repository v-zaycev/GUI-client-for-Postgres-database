from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QToolButton, QMenu)
from PyQt6.QtGui import QAction
from sources.base_client import PgsqlClient
from sources.main_window.basic_widget import BasicWidget
from sources.main_window.dialogs.ward_edit_dialog import AddWardDialog
from sources.main_window.dialogs.diagnosis_edit_dialog import AddDiagnosisDialog



class DirectoriesWidget(BasicWidget):
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.title_label = QLabel("Справочники")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(self.title_label)
        

        # Панель кнопок
        self.buttons_layout = self.init_buttons()
        self.layout().addLayout(self.buttons_layout)
        self.load_button.clicked.connect(self.load_data)
        self.update_button.clicked.connect(lambda: self.show_add_dialog(self.get_selected_rows_data(self.table)))
        self.insert_button.clicked.connect(lambda: self.show_add_dialog())
        self.delete_button.clicked.connect(self.delete_rows)

        self.tool_btn = QToolButton()
        self.tool_btn.setText("Выбор справочника")  # Текст кнопки
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
        if self.current_table_name == 'wards_view':
            self.title_label.setText("Палаты")
        elif self.current_table_name == 'diagnosis':
            self.title_label.setText("Диагнозы")
    
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