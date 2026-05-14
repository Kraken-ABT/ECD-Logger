from modules.parser import parse_time_string

_MAX_SERVER_NAME_LENGTH = 50

STATUS_EMOJI = {
    "success": "✅ ЧИСТ",
    "warning": "⚠️ ПОДОЗРИТЕЛЬНЫЙ",
    "danger": "❌ ЧИТЕР",
    "hack": "🛡 ОБХОД ECD"
}

def format_ecd_report(report, target_srv=None):
    status = STATUS_EMOJI.get(report.get('result_status'), "❓ НЕИЗВЕСТНО")
    host = report.get('hostname', 'N/A')

    if target_srv and target_srv.lower() in host.lower():
        srv_type = "🎯 ЦЕЛЕВОЙ"
    elif not host or host == 'N/A':
        srv_type = "🔒 СКРЫТ"
    else:
        srv_type = "📡 ДРУГОЙ"

    if len(host) > _MAX_SERVER_NAME_LENGTH:
        host = host[:_MAX_SERVER_NAME_LENGTH-3] + "..."

    scan_id = report.get('scan_id', '?')

    raw_time = report.get('report_time', report.get('time', '?'))
    if 'сегодня' in raw_time or 'вчера' in raw_time:
        display_time = parse_time_string(raw_time)
    else:
        display_time = raw_time

    lines = [
        f"{'=' * 60}",
        f"НОВЫЙ ОТЧЁТ #{scan_id}",
        f"👤 Игрок: {report.get('nick', '?')}",
        f"📊 Статус: {status}",
        f"🕐 Время: {display_time}",
        f"{srv_type} Сервер: {host}",
        f"🌐 IP: {report.get('user_ip', '?')}",
        f"🔗 Ссылка: {report.get('url', 'N/A')}",
        f"{'=' * 60}"
    ]

    return "\n".join(lines)

def show_stats(stats):
    if not stats:
        print("Статистика недоступна")
        return
    print(f"\n┌{'─'*40}┐\n│{' СТАТИСТИКА БД '.center(40)}│\n├{'─'*40}┤")
    print(f"│ Всего отчетов: {stats['total']:<19}│")
    if stats.get('by_status'):
        print(f"├{'─'*40}┤")
        for st, cnt in stats['by_status'].items():
            e = {"success":"✅","warning":"⚠️","danger":"❌"}.get(st, "❓")
            print(f"│ {e} {st}: {cnt:<22}│")
    print(f"└{'─'*40}┘")
    if stats.get('last_report'):
        last = stats['last_report']
        print(f"\n📌 Последний: #{last[0]} - {last[1]} ({last[2]})")
        print(f"   Сервер: {last[3]}")
    if stats.get('by_day'):
        print("\n📅 Последние 7 дней:")
        for day, cnt in stats['by_day']:
            print(f"   {day}: {cnt}")

def format_gamecms_event(entry):
    player = entry.get('player_name', '?')
    status = entry.get('result_status', 'unknown')
    report_id = entry.get('report_id', 'N/A')
    return (f"[GameCMS] Запись #{entry['id']}: {player} "
            f"| Статус: {status} | Report ID: {report_id}")