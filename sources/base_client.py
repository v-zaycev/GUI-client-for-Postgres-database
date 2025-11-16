import psycopg2
import configparser
import bcrypt
class PgsqlClient:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        self.db_host = config['database']['host']
        self.db_port = config['database'].getint('port')
        self.db_base = config['database']['database']
        self.db_user = config['database']['username']
        self.db_pass = config['database']['password']
        self.connection = None
 
    def get_connection(self):
        return psycopg2.connect(
            host = self.db_host,
            port = self.db_port,
            database = self.db_base,
            user = self.db_user,
            password = self.db_pass,
        )
    
    def insert_user(self, attributes,  username : str, password : str, role : str):
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                vals = f"'{username}', '{str(bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt()), 'utf8')}', '{role}' "
                query = f"INSERT INTO users ({', '.join(attributes)}) VALUES ({vals})"
                cursor.execute(query)
                self.connection.commit()
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise
    
    def edit_user(self, attributes : list,  data : list, id : int | None):
        if data[1] != "":
            data[1] = bcrypt.hashpw(data[1].encode('utf-8'), bcrypt.gensalt())
            data[1] = data[1].decode('utf-8')
        else:
            attributes = [attributes[i] for i in [0,2]]
            data = [data[i] for i in [0,2]]
        if id is None:
            self.insert(attributes, "users", data)
        else:
            self.update(attributes, "users", data, id)
            
                


    def log_in(self, app_username : str, app_password : str) -> bool:
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT password_hash FROM users WHERE username = \'{app_username}\'")
                users_hash = cursor.fetchall()
                if len(users_hash) == 1:
                    result = bcrypt.checkpw(bytes(app_password, "utf-8"), bytes(users_hash[0][0], "utf-8"))
                    if result:
                        print("success log")
                        cursor.execute(f"CALL set_role('{app_username}')")
                        self.connection.commit()
                        return True
                    else:
                        print("incorrect password")
                        return False
                else:
                    print("incorrect number of users")
                    return False
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise
            
    def log_out(self):
        if self.connection is not None:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("SET ROLE waitroom_role")
            except psycopg2.Error:
                self.connection = None
    
    def get_table_rights(self, table_name : str) -> dict:
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT * 
                    FROM permissions_table
                    WHERE  table_name = \'{table_name}\'""")
                data = cursor.fetchall()
                if len(data) != 1:
                    return None
                result = {
                    "select" : data[0][1],
                    "insert" : data[0][2],
                    "update" : data[0][3],
                    "delete" : data[0][4]
                }
                return result
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise

    def select(self, attributes: list[str], table: str, where : str = None) -> tuple:
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                query = f"SELECT {', '.join(attributes)} FROM {table}"
                if where is not None:
                    query += " WHERE " + where
                cursor.execute(query)
                result = (cursor.fetchall(), cursor.description)
                self.connection.commit()
                return result
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise
    
    def update(self, attributes: list[str], table: str, data: list[str], id : int):
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                result = [f"{k} = '{v}'" for k, v in zip(attributes, data)]
                query = f"UPDATE {table} SET {', '.join(result)} WHERE id = {id}"
                cursor.execute(query)
                self.connection.commit()
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise
    
    def insert(self, attributes: list[str], table: str, data: list):
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                placeholders = ', '.join(['%s'] * len(data))
                query = f"INSERT INTO {table} ({', '.join(attributes)}) VALUES ({placeholders})"
                cursor.execute(query, data)
                self.connection.commit()
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise
    
    def delete(self, attributes: list[str], table: str):
        try:
            if self.connection is None:
                self.connection = self.get_connection()
            with self.connection.cursor() as cursor:
                query = f"DELETE FROM {table} WHERE id IN ({', '.join(attributes)})"
                cursor.execute(query)
                self.connection.commit()
        except psycopg2.Error:
            try:
                self.connection.rollback()
            except psycopg2.Error:
                self.connection = None
                raise
            raise
