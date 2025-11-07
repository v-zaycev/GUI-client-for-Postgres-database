from PyQt6.QtWidgets import ( QHeaderView, QWidget, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QMessageBox, QHBoxLayout)
from PyQt6.QtCore import Qt
from main_window.names_conversion import names_conversion

class BasicWidget(QWidget):
    pgsql_client = None
    rights = None
    current_table_name = None
    table = None

    @staticmethod
    def init_table() -> QTableWidget:
        table = QTableWidget()
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        horizontal_header = table.horizontalHeader()
        vertical_header = table.verticalHeader()
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return table

    def init_buttons(self) -> QHBoxLayout:
        buttons_layout = QHBoxLayout()

        self.load_button = QPushButton("Обновить данные")
        self.load_button.setEnabled(True)
        self.load_button.setFixedWidth(120)
        buttons_layout.addWidget(self.load_button)
        
        # Кнопки
        self.insert_button = QPushButton("Добавить запись")
        self.update_button = QPushButton("Изменить запись") 
        self.delete_button = QPushButton("Удалить записи")
        
        self.insert_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.insert_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        self.update_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        self.delete_button.setStyleSheet("color: transparent; background-color: transparent; border: none;")
        
        # Фиксируем ширину для аккуратного вида
        self.insert_button.setFixedWidth(120)
        self.update_button.setFixedWidth(120)
        self.delete_button.setFixedWidth(120)
        
        buttons_layout.addWidget(self.insert_button)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        
     #   self.layout().addLayout(buttons_layout)
        
        return buttons_layout

    def set_buttons_states(self):
        if self.rights[self.current_table_name]["insert"]:
            self.insert_button.setStyleSheet("QPushButton {}")
            self.insert_button.setEnabled(True)
        if self.rights[self.current_table_name]["update"]:
            self.update_button.setStyleSheet("QPushButton {}")
            self.update_button.setEnabled(False)
        if self.rights[self.current_table_name]["delete"]:
            self.delete_button.setStyleSheet("QPushButton {}")
            self.delete_button.setEnabled(False)

    def update_buttons_states(self, selected_count : int):
        if selected_count == 1:
            if self.rights[self.current_table_name]["update"]:
                self.update_button.setEnabled(True)
            if self.rights[self.current_table_name]["delete"]:
                self.delete_button.setEnabled(True)
        elif selected_count > 1:
            self.update_button.setEnabled(False)
            if self.rights[self.current_table_name]["delete"]:
                self.delete_button.setEnabled(True)
        else:
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    @staticmethod    
    def get_column_values_from_selected(table : QTableWidget, column : int = 0) -> list[str]:
        return [table.item(row.row(), column).text() 
                for row in table.selectionModel().selectedRows()
                if table.item(row.row(), column) is not None]

    @staticmethod
    def get_selected_rows_data(table : QTableWidget) -> list[list[str]]:
        selected_data = []
        selected_indexes = table.selectionModel().selectedRows()

        for index in selected_indexes:
            row = index.row()
            row_data = []

            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")
        
            selected_data.append(row_data)
        
        return selected_data

    def delete_rows(self):
        ids = self.get_column_values_from_selected(self.table)
        self.pgsql_client.delete(ids, self.current_table_name)
        data, description = self.pgsql_client.select(['*'], self.current_table_name)
        self.table.clearSelection()
        self.show_data(data, description)
    
    def show_data(self, data, description):
        try:
            # Настраиваем таблицу
            column_names = [names_conversion[self.current_table_name][desc[0]] for desc in description]
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(column_names))
            self.table.setHorizontalHeaderLabels(column_names)
            
            # Заполняем таблицу данными
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value) if value is not None else ""))
            
            # Автоподбор размера колонок
            self.table.resizeColumnsToContents()
            
            # Обновляем статус
            self.status_label.setText(f"Загружено записей: {len(data)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
            self.status_label.setText("Ошибка при загрузке данных")

    def load_data(self):
        data, description = self.pgsql_client.select(['*'], self.current_table_name)
        self.show_data(data, description)
