import time
import random
import logging
import uuid
import json
from datetime import datetime
from modules.parser import ECDParser, parse_time_string
from modules.database_sqlite import ReportsDB
from modules.formatter import format_ecd_report

logger = logging.getLogger(__name__)

_SCAN_MODES = {
    1: {"name": "ТОЛЬКО ЦЕЛЕВОЙ СЕРВЕР", "include_hidden": False, "monitor_all": False},
    2: {"name": "ВСЕ СЕРВЕРА", "include_hidden": True,  "monitor_all": True},
    3: {"name": "ЦЕЛЕВОЙ + СКРЫТЫЕ СЕРВЕРА", "include_hidden": True, "monitor_all": False}
}

class ECDMonitor:
    def __init__(self, cfg, db: ReportsDB, notifier):
        self.cfg = cfg
        self.db = db
        self.notifier = notifier
        self.parser = ECDParser(cfg)
        self.target = cfg.get('EL_Target', '').strip()
        self.limit = cfg.get('EL_MaxReportsPerScan', 150)
        mode = cfg.get('EL_Mode', 1)
        mc = _SCAN_MODES.get(mode, _SCAN_MODES[1])
        self.monitor_all = mc["monitor_all"]
        self.inc_hidden = mc["include_hidden"]
        self.mode_name = mc["name"]
        self.checks = self.new = self.hid = self.oth = 0

    def _accept(self, report):
        if self.monitor_all:
            return True
        host = report.get('hostname', '')
        if host in ('N/A', '-', '', None):
            return self.inc_hidden
        return bool(self.target and self.target.lower() in host.lower())

    def _process_archive_and_counts(self, local_id, scan_id_int):
        get_drivers = self.cfg.get('EL_GetDrivers', 0)
        get_modules = self.cfg.get('EL_GetModules', 0)
        get_processes = self.cfg.get('EL_GetProcesses', 0)
        if not (get_drivers or get_modules or get_processes):
            return None

        details = self.parser.fetch_archive(scan_id_int)
        if details is None:
            return None
        if isinstance(details, dict) and details.get('error') == 'blocked':
            return 'blocked'

        try:
            data = details.get('data', {})
        except AttributeError:
            return None

        counts = {'drivers': 0, 'modules': 0, 'processes': 0}
        if get_drivers and 'drivers' in data:
            self.db.save_drivers(local_id, data['drivers'])
            counts['drivers'] = len(data['drivers'])
        if get_modules and 'modules' in data:
            self.db.save_modules(local_id, data['modules'])
            counts['modules'] = len(data['modules'])
        if get_processes and 'processes' in data:
            self.db.save_processes(local_id, data['processes'])
            counts['processes'] = len(data['processes'])
        return counts

    def _process_items(self, items, is_parsed=True):
        new_c = hid_c = oth_c = 0
        if self.limit > 0 and len(items) > self.limit:
            items = items[:self.limit]

        for item in items:
            rep = item if is_parsed else self.parser.parse_item(item)
            if not rep:
                continue
            if not self._accept(rep):
                if rep.get('hostname') in ('N/A', '-', '', None):
                    hid_c += 1
                else:
                    oth_c += 1
                continue

            scan_id_int = rep['report_id']
            scan_id = str(scan_id_int)

            if self.db.exists(scan_id):
                continue

            local_id = f"i{uuid.uuid4().hex[:8]}_"

            try:
                raw = json.dumps(rep, ensure_ascii=False, default=str)
            except Exception:
                raw = None

            report_db = {
                'scan_id': scan_id,
                'nick': rep.get('nick'),
                'result_status': rep.get('result_status'),
                'time': rep.get('time'),
                'hostname': rep.get('hostname'),
                'user_ip': rep.get('user_ip'),
                'url': rep.get('url'),
                'raw_data': raw
            }

            self.db.save(local_id, report_db, source='fungun')

            print(format_ecd_report(report_db, self.target))
            logger.info(f"✅ #{local_id} (scan #{scan_id}) - {rep['nick']} ({rep['result_status']})")

            self.notifier.send_new_report(report_db)
            new_c += 1

            result = self._process_archive_and_counts(local_id, scan_id_int)
            if result == 'blocked':
                self.db.add_soon_scan(local_id, scan_id, status='in process', attempts=1)
                print("⛔ Архив заблокирован (IP), отчёт отложен.")
            elif isinstance(result, dict):
                print(f"📦 Драйверы: {result['drivers']}, Модули: {result['modules']}, Процессы: {result['processes']}")

            time.sleep(self.cfg.get('EL_RequestDelay', 0.1))

        return new_c, hid_c, oth_c

    def _process_batch(self):
        needed = self.limit if self.limit > 0 else 150
        parsed = self.parser.fetch_many(target_count=needed, page_size=50)
        if not parsed:
            return 0, 0, 0
        return self._process_items(parsed, is_parsed=True)

    def run(self):
        logger.info(f"{'='*60}\nРежим: {self.mode_name}\nЦель: {self.target or 'ВСЕ'}\n"
                    f"Интервал: {self.cfg['min_interval']}-{self.cfg['max_interval']} сек\n"
                    f"Лимит: {self.limit if self.limit>0 else 'без ограничений'}\n{'='*60}")
        print(f"\n📋 Режим: {self.mode_name}\n🎯 Сервер: {self.target or 'ВСЕ'}\n⏎ Ctrl+C для остановки\n")

        while True:
            try:
                self.checks += 1
                t0 = time.time()
                n, h, o = self._process_batch()
                self.new += n
                self.hid += h
                self.oth += o
                total_in_db = self.db.stats()['total'] if self.db.stats() else 0
                print(f"\n📊 Проверка #{self.checks}: {time.time()-t0:.2f} сек | В БД: {total_in_db} | Новых: {n}")
                delay = random.randint(self.cfg['min_interval'], self.cfg['max_interval'])
                logger.info(f"Следующая проверка в {datetime.fromtimestamp(time.time()+delay).strftime('%H:%M:%S')}")
                print(f"⏳ Ожидание {delay//60} мин {delay%60} сек...")
                time.sleep(delay)

            except KeyboardInterrupt:
                print(f"\n{'='*60}\nПроверок: {self.checks}\nНайдено: {self.new}\n{'='*60}")
                if self.cfg.get('EL_ShowStatsOnStart', 0):
                    from modules.formatter import show_stats
                    show_stats(self.db.stats())
                break
            except Exception as e:
                logger.error(f"Ошибка в сканере: {e}")
                time.sleep(60)