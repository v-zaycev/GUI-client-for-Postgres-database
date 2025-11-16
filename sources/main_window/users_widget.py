from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QMessageBox)
import psycopg2
from sources.base_client import PgsqlClient
from sources.main_window.basic_widget import BasicWidget
from sources.main_window.dialogs.user_dialog import AddUserDialog

class UsersWidget(BasicWidget):
    def __init__(self, db_client : PgsqlClient):
        super().__init__()
        self.pgsql_client = db_client
        # Создаем layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Заголовок
        title_label = QLabel("Пользователи")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px;")
        layout.addWidget(title_label)
        
        # Панель кнопок
        self.buttons_layout = self.init_buttons()
        self.layout().addLayout(self.buttons_layout)
        
        # Таблица для отображения данных
        self.table = self.init_table()
        self.table.itemSelectionChanged.connect(lambda: self.update_buttons_states(len(self.table.selectionModel().selectedRows())))
        layout.addWidget(self.table)

        
        # Статус
        self.status_label = QLabel("Нажмите кнопку для загрузки данных")
        layout.addWidget(self.status_label)
        
        # Загружаем данные при старте
        self.current_table_name = "users"
        data, description = self.pgsql_client.select(['*'], 'users', "user_role != 'super_role'")
        self.rights = {"users" : self.pgsql_client.get_table_rights("users")}
        self.set_buttons_states()
        self.load_button.clicked.connect(self.load_data)
        self.update_button.clicked.connect(lambda: self.show_add_dialog(self.get_selected_rows_data(self.table)))
        self.insert_button.clicked.connect(lambda: self.show_add_dialog())
        self.delete_button.clicked.connect(self.delete_rows)
        self.show_data(data, description)

    def show_add_dialog(self, old : list[list[str]] = None):
        try:
            if old is None or len(old) == 0:
                data = None
            else:
                data = {
                    "id" : old[0][0],
                    "username" : old[0][1],
                    "password_hash" : old[0][2],
                    "user_role" : old[0][3],
                }
            dialog = AddUserDialog(self.pgsql_client, data)
            if dialog.exec():
                data = dialog.get_new_data()
                dialog.edit_user(data)
            data, description = self.pgsql_client.select(['*'], 'users', "user_role != 'super_role'")
            self.table.clearSelection()
            self.show_data(data, description)
        except psycopg2.Error as e:
            QMessageBox.critical(None, "Ошибка базы данных", str(e.diag.message_primary))
        except Exception:
            QMessageBox.critical(None, "Ошибка", "Ошибка соединения")
