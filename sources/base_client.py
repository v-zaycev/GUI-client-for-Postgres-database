import psycopg2
import configparser
import bcrypt
class PgsqlClient:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('sources\\config.ini', encoding='utf-8')
        self.db_host = config['database']['host']
        self.db_port = config['database'].getint('port')
        self.db_base = config['database']['database']
        self.db_user = config['database']['username']
        self.db_pass = config['database']['password']
        self.connection = self.get_connection()
 
    def get_connection(self):
        return psycopg2.connect(
            host = self.db_host,
            port = self.db_port,
            database = self.db_base,
            user = self.db_user,
            password = self.db_pass
        )
    
    def log_in(self, app_username : str, app_password : str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT password_hash FROM users WHERE username = \'{app_username}\'")
            users_hash = cursor.fetchall()
            if len(users_hash) == 1:
                result = bcrypt.checkpw(bytes(app_password, "utf-8"), bytes(users_hash[0][0], "utf-8"))
                if result:
                    print("success log")
                    cursor.execute(f"CALL set_role(\'{app_username}\')")
                    return True
                else:
                    print("incorrect password")
                    return False
            else:
                print("incorrect number of users")
                return False
            
    def log_out(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SET ROLE waitroom_role")
    
    def get_table_rights(self, table_name : str) -> list:
        with self.connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT * 
                FROM permissions_table
                WHERE  table_name = \'{table_name}\'""")
            return cursor.fetchall()
        pass

    def select(self):
        pass
    
    def update(self):
        pass
    
    def insert():
        pass
    
    def delete():
        pass

if __name__ == "__main__":
    with open('sources\\config.ini', 'rb') as f:
        raw_content = f.read()
        print("Raw bytes:", raw_content)
    client = PgsqlClient()
    client.log_in('basic_user2', 'qwerty2')
    pass