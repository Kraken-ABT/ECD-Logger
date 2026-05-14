import mysql.connector
from mysql.connector import Error

class MySQLConnection:
    def __init__(self, host, port, user, password, database):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
        self.conn = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            return self.conn
        except Error as e:
            print(f"[MySQL] Ошибка подключения: {e}")
            return None

    def fetch_last_log(self):
        if not self.conn or not self.conn.is_connected():
            if not self.connect():
                return None
        try:
            cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT id, timestamp, event_type, player_name, player_authid,
                       player_ip, admin_name, result_type, result_status, report_id,
                       os_type, server_id, member_id, member_login
                FROM ecd_logs
                ORDER BY id DESC LIMIT 1
            """
            cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            print(f"[MySQL] Ошибка запроса: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()