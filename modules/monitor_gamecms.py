import time
import threading
from modules.database_mysql import MySQLConnection
from modules.formatter import format_gamecms_event
import json

class GameCMSMonitor(threading.Thread):
    def __init__(self, cfg, db_sqlite, notifier):
        super().__init__(daemon=True, name="GameCMSMonitor")
        self.cfg = cfg
        self.db_sqlite = db_sqlite
        self.notifier = notifier
        self.mysql = MySQLConnection(
            host=cfg['GameCMS_DB_Host'],
            port=cfg['GameCMS_DB_Port'],
            user=cfg['GameCMS_DB_User'],
            password=cfg['GameCMS_DB_Pass'],
            database=cfg['GameCMS_DB_Name']
        )
        self.last_id = 0
        self.cache = {}

    def run(self):
        print("[GameCMS] Монитор запущен")
        while True:
            try:
                entry = self.mysql.fetch_last_log()
                if not entry:
                    time.sleep(5)
                    continue

                eid = entry['id']
                if eid > self.last_id:
                    self.last_id = eid
                    self.cache[eid] = entry['result_status']
                    print(f"\n[GameCMS] Новая запись #{eid}: {entry['player_name']} ({entry['result_status']})")
                    self.notifier.send_gamecms_event(entry)
                    self._save_to_sqlite(entry)

                elif eid == self.last_id:
                    old_status = self.cache.get(eid)
                    if old_status and old_status != entry['result_status']:
                        self.cache[eid] = entry['result_status']
                        print(f"[GameCMS] Изменение статуса #{eid}: {old_status} -> {entry['result_status']}")
                        self.notifier.send_gamecms_status_change(entry, old_status)
                time.sleep(5)

            except Exception as e:
                print(f"[GameCMS] Ошибка: {e}")
                time.sleep(10)

    def _save_to_sqlite(self, entry):
        local_id = f"gcms_{entry['id']}"
        scan_id = str(entry['report_id']) if entry.get('report_id') else f"gcms_{entry['id']}"
        if self.db_sqlite.exists(scan_id):
            return
        report = {
            'scan_id': scan_id,
            'nick': entry.get('player_name', 'Unknown'),
            'result_status': entry.get('result_status', 'unknown'),
            'time': str(entry.get('timestamp', '')),
            'hostname': entry.get('server_id', 'N/A'),
            'user_ip': entry.get('player_ip', 'N/A'),
            'url': '',
        }
        self.db_sqlite.save(local_id, report, source='gamecms')