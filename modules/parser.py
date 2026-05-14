import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ua import user_agents

_S_B_FG = "https://fungun.net"
_S_A_FG = "https://fungun.net/ecd/ajax/ecd_front.php?method=list"
_S_R_FG = "https://fungun.net/ecd/list/"
_DEFAULT_UA = "ECDLogger/1.4.3"


def parse_time_string(s, now=None):
    if now is None:
        now = datetime.now()
    s = s.strip()
    if 'сегодня' in s:
        time_part = s.split(' в ')[-1].strip()
        return f"{now.day:02d}.{now.month:02d}.{now.year} {time_part}"
    elif 'вчера' in s:
        yesterday = now - timedelta(days=1)
        time_part = s.split(' в ')[-1].strip()
        return f"{yesterday.day:02d}.{yesterday.month:02d}.{yesterday.year} {time_part}"
    return s


class ECDParser:
    def __init__(self, cfg):
        self.cfg = cfg
        self.s = requests.Session()
        self.s.verify = bool(cfg.get('EL_VerifySSL', 0))
        if not self.s.verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": _S_R_FG
        }
        if cfg.get('EL_UseCustomUA', 1):
            headers["User-Agent"] = random.choice(user_agents) if cfg.get('EL_RandomUA', 1) else _DEFAULT_UA
        self.s.headers.update(headers)
        self._visit_referer()

    def _visit_referer(self):
        try:
            self.s.get(_S_R_FG, timeout=self.cfg.get('EL_RequestTimeout', 10))
        except Exception:
            pass

    def fetch(self):
        for attempt in range(2):
            try:
                r = self.s.get(_S_A_FG, timeout=self.cfg.get('EL_RequestTimeout', 10))
                r.raise_for_status()
                return r.json()
            except requests.RequestException:
                return None
            except json.JSONDecodeError:
                if attempt == 0 and "Access Denied" in r.text:
                    self._visit_referer()
                    continue
                return None
        return None

    def fetch_many(self, target_count=150, page_size=50):
        collected = []
        start = last_id = 0
        while len(collected) < target_count:
            params = {
                'method': 'list', 'draw': 1, 'start': start, 'length': page_size,
                'last_id': last_id, 'search[value]': '', 'search[regex]': 'false'
            }
            cols = ['nick','user_ip','hostname','result_status','before','time','more']
            for i, col in enumerate(cols):
                params[f'columns[{i}][data]'] = col
                params[f'columns[{i}][searchable]'] = 'true' if i < 4 else 'false'
                params[f'columns[{i}][orderable]'] = 'false' if i != 5 else 'true'
            try:
                resp = self.s.get(_S_A_FG, params=params, timeout=self.cfg.get('EL_RequestTimeout', 10))
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                break
            items = data.get('data', [])
            if not items:
                break
            last_id = items[-1].get('DT_RowData', {}).get('report_id', 0) or items[-1].get('report_id', 0)
            for item in items:
                rep = self.parse_item(item)
                if rep and rep['report_id']:
                    collected.append(rep)
                    if len(collected) >= target_count:
                        break
            start += page_size
            if len(items) < page_size:
                break
            time.sleep(1)
        return collected[:target_count]

    @staticmethod
    def parse_item(item):
        def p(html, sel=None, attr=None):
            try:
                el = BeautifulSoup(html, 'html.parser')
                target = el.find(sel) if sel else el
                return target.get(attr) if attr else target.get_text().strip() if target else "N/A"
            except:
                return "N/A"

        more = item.get('more', '')
        url_path = p(more, 'a', 'href')
        url = f"{_S_B_FG}{url_path}" if url_path != "N/A" else "N/A"

        raw_time = item.get('time', 'N/A')
        formatted_time = parse_time_string(raw_time) if raw_time != 'N/A' else raw_time

        return {
            'report_id': int(item.get('DT_RowData', {}).get('report_id', 0)),
            'nick': p(item.get('nick', ''), 'a'),
            'result_status': p(item.get('result_status', ''), 'span', 'data-result_status') or 'unknown',
            'time': formatted_time,
            'hostname': p(item.get('hostname', '')) or 'N/A',
            'user_ip': (p(item.get('user_ip', '')).split()[-1] if p(item.get('user_ip', '')) else 'N/A'),
            'url': url
        }

    def fetch_archive(self, scan_report_id):
        try:
            resp = self.s.post(
                "https://fungun.net/ecd/ajax/ecd_front.php",
                data={'method': 'archive', 'report_id': scan_report_id},
                timeout=self.cfg.get('EL_RequestTimeout', 10)
            )
            if resp.status_code == 403 or "Access Denied" in resp.text:
                return {'error': 'blocked'}
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if getattr(e.response, 'status_code', None) == 403:
                return {'error': 'blocked'}
            return None
        except Exception:
            return None
