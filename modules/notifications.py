import requests
import logging
import time
from modules.formatter import STATUS_EMOJI

logger = logging.getLogger(__name__)

def escape_html(text: str) -> str:
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

class BaseNotifier:
    def send_new_report(self, report):
        pass
    def send_gamecms_event(self, entry):
        pass
    def send_gamecms_status_change(self, entry, old_status):
        pass

class TelegramNotifier(BaseNotifier):
    def __init__(self, token, chat_id, proxy=None, use_proxy=False):
        self.token = token
        self.chat_id = chat_id
        self.proxy = proxy if use_proxy else None
        self._last_error_time = 0

    def _send(self, text, parse_mode='HTML'):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'disable_web_page_preview': True
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode

        proxies = None
        if self.proxy:
            proxies = {'https': self.proxy}

        for attempt in range(1, 4):
            try:
                resp = requests.post(url, json=payload, timeout=15, proxies=proxies)
                resp.raise_for_status()
                return
            except requests.exceptions.Timeout:
                if attempt == 3:
                    self._log_error("Telegram timeout after 3 attempts, message skipped")
                else:
                    time.sleep(2 * attempt)
            except requests.exceptions.ConnectionError as e:
                if attempt == 3:
                    self._log_error(f"Telegram connection error: {e}")
                else:
                    time.sleep(5 * attempt)
            except requests.exceptions.HTTPError as e:
                if resp is not None and resp.status_code == 400:
                    if parse_mode:
                        payload.pop('parse_mode', None)
                        parse_mode = None
                        continue
                self._log_error(f"Telegram HTTP error: {e}")
                break
            except Exception as e:
                self._log_error(f"Telegram unknown error: {e}")
                break

    def _log_error(self, msg):
        now = time.time()
        if now - self._last_error_time > 300:
            logger.error(msg)
            self._last_error_time = now

    def send_new_report(self, report):
        status_raw = report.get('result_status', 'unknown')
        status_text = STATUS_EMOJI.get(status_raw, f"❓ {status_raw}")
        nick = escape_html(str(report.get('nick', '?')))
        host = escape_html(str(report.get('hostname', 'N/A')))
        ip = report.get('user_ip', 'N/A')
        scan_id = report.get('scan_id', '?')
        url = report.get('url', '')
        link_line = f'\n🔗 <a href="{url}">Ссылка на отчёт</a>' if url and url != 'N/A' else ''

        msg = (
            f"🆕 <b>Новый отчёт #{scan_id}</b>\n"
            f"👤 {nick}\n"
            f"📊 Статус: {status_text}\n"
            f"🖥 Сервер: {host}\n"
            f"🌐 IP: {ip}"
            f"{link_line}"
        )
        self._send(msg, parse_mode='HTML')

    def send_gamecms_event(self, entry):
        player = escape_html(str(entry.get('player_name', '?')))
        status_raw = entry.get('result_status', 'unknown')
        status_text = STATUS_EMOJI.get(status_raw, status_raw)
        report_id = entry.get('report_id', 'N/A')
        msg = (
            f"🎮 <b>GameCMS: новый отчёт</b>\n"
            f"👤 {player}\n"
            f"📊 Статус: {status_text}\n"
            f"🔎 ID отчёта: {report_id}"
        )
        self._send(msg, parse_mode='HTML')

    def send_gamecms_status_change(self, entry, old_status):
        player = escape_html(str(entry.get('player_name', '?')))
        old_text = STATUS_EMOJI.get(old_status, old_status)
        new_text = STATUS_EMOJI.get(entry.get('result_status', 'unknown'),
                                    entry.get('result_status', 'unknown'))
        msg = (
            f"🔄 <b>GameCMS: статус изменён</b>\n"
            f"👤 {player}\n"
            f"📉 {old_text} → {new_text}"
        )
        self._send(msg, parse_mode='HTML')

class VKNotifier(BaseNotifier):
    def __init__(self, token, peer_id):
        self.token = token
        self.peer_id = peer_id

    def _send(self, message):
        url = "https://api.vk.com/method/messages.send"
        params = {
            'access_token': self.token,
            'peer_id': self.peer_id,
            'message': message,
            'random_id': 0,
            'v': '5.199'
        }
        try:
            requests.post(url, params=params, timeout=10)
        except Exception as e:
            logger.error(f"VK send error: {e}")

    def send_new_report(self, report):
        msg = f"🆕 Новый отчёт #{report['scan_id']}\nИгрок: {report['nick']}\nСтатус: {report['result_status']}\nСервер: {report['hostname']}"
        self._send(msg)

    def send_gamecms_event(self, entry):
        msg = f"🎮 GameCMS: {entry['player_name']}\nСтатус: {entry['result_status']}"
        self._send(msg)

    def send_gamecms_status_change(self, entry, old_status):
        msg = f"🔄 GameCMS: {entry['player_name']}\n{old_status} → {entry['result_status']}"
        self._send(msg)

class CompositeNotifier(BaseNotifier):
    def __init__(self, notifiers):
        self.notifiers = notifiers

    def send_new_report(self, report):
        for n in self.notifiers:
            n.send_new_report(report)

    def send_gamecms_event(self, entry):
        for n in self.notifiers:
            n.send_gamecms_event(entry)

    def send_gamecms_status_change(self, entry, old_status):
        for n in self.notifiers:
            n.send_gamecms_status_change(entry, old_status)

def get_notifier(cfg):
    notifiers = []
    if cfg.get('Telegram_Enable') and cfg.get('Telegram_Token') and cfg.get('Telegram_ChatID'):
        use_proxy = cfg.get('Telegram_UseProxy', 0)
        proxy = cfg.get('Telegram_Proxy', '') if use_proxy else None
        notifiers.append(TelegramNotifier(
            cfg['Telegram_Token'],
            cfg['Telegram_ChatID'],
            proxy,
            use_proxy=bool(use_proxy)
        ))
        print("Уведомления Telegram включены.")
    if cfg.get('VK_Enable') and cfg.get('VK_Token') and cfg.get('VK_PeerID'):
        notifiers.append(VKNotifier(cfg['VK_Token'], cfg['VK_PeerID']))
        print("Уведомления VK включены.")
    if not notifiers:
        return BaseNotifier()   # пустой, ничего не делает
    return CompositeNotifier(notifiers)