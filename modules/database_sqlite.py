import os
import sqlite3
import uuid
from modules.parser import parse_time_string

class ReportsDB:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()

    def _init_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    local_id TEXT PRIMARY KEY,
                    source TEXT DEFAULT 'fungun',
                    scan_id TEXT UNIQUE,
                    nick TEXT,
                    result_status TEXT,
                    report_time TEXT,
                    hostname TEXT,
                    user_ip TEXT,
                    url TEXT,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''CREATE TABLE IF NOT EXISTS drivers (
                local_id TEXT, name TEXT, description TEXT, path TEXT,
                FOREIGN KEY(local_id) REFERENCES reports(local_id)
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS modules (
                local_id TEXT, name TEXT, path TEXT,
                FOREIGN KEY(local_id) REFERENCES reports(local_id)
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS processes (
                local_id TEXT, name TEXT, count INTEGER, path TEXT,
                FOREIGN KEY(local_id) REFERENCES reports(local_id)
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS soon_scan (
                local_id TEXT, scan_id TEXT,
                status TEXT DEFAULT 'in process',
                attempts INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_attempt TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(local_id) REFERENCES reports(local_id)
            )''')

    def exists(self, scan_id):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT 1 FROM reports WHERE scan_id=? LIMIT 1", (scan_id,))
            return cur.fetchone() is not None

    def save(self, local_id, report, source='fungun'):
        scan_id = report.get('scan_id')
        nick = report.get('nick')
        result_status = report.get('result_status')
        raw_time = report.get('time', report.get('report_time'))
        if raw_time and ('сегодня' in raw_time or 'вчера' in raw_time):
            report_time = parse_time_string(raw_time)
        else:
            report_time = raw_time

        hostname = report.get('hostname')
        user_ip = report.get('user_ip')
        url = report.get('url', '')
        raw_data = report.get('raw_data')

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO reports
                (local_id, source, scan_id, nick, result_status, report_time,
                 hostname, user_ip, url, raw_data)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            ''', (local_id, source, scan_id, nick, result_status,
                  report_time, hostname, user_ip, url, raw_data))

    def save_drivers(self, local_id, drivers):
        if not drivers:
            return
        with sqlite3.connect(self.db_path) as conn:
            for name, info in drivers.items():
                conn.execute("INSERT INTO drivers (local_id, name, description, path) VALUES (?,?,?,?)",
                             (local_id, name, info.get('desc', ''), info.get('path', '')))

    def save_modules(self, local_id, modules):
        if not modules:
            return
        with sqlite3.connect(self.db_path) as conn:
            for name, info in modules.items():
                conn.execute("INSERT INTO modules (local_id, name, path) VALUES (?,?,?)",
                             (local_id, name, info.get('path', '')))

    def save_processes(self, local_id, processes):
        if not processes:
            return
        with sqlite3.connect(self.db_path) as conn:
            for name, info in processes.items():
                conn.execute("INSERT INTO processes (local_id, name, count, path) VALUES (?,?,?,?)",
                             (local_id, name, info.get('count', 0), info.get('path', '')))

    def add_soon_scan(self, local_id, scan_id, status='in process', attempts=1):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''INSERT OR REPLACE INTO soon_scan (local_id, scan_id, status, attempts)
                            VALUES (?,?,?,?)''', (local_id, scan_id, status, attempts))

    def stats(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
                by_status = dict(conn.execute(
                    "SELECT result_status, COUNT(*) FROM reports GROUP BY result_status").fetchall())
                last = conn.execute(
                    "SELECT scan_id, nick, report_time, hostname FROM reports ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
                by_day = conn.execute(
                    "SELECT DATE(created_at) AS day, COUNT(*) FROM reports "
                    "WHERE created_at >= DATE('now','-7 days') GROUP BY day ORDER BY day DESC"
                ).fetchall()
            return {'total': total, 'by_status': by_status, 'last_report': last, 'by_day': by_day}
        except Exception:
            return None