import os

DEFAULTS = {
    'EL_DataBasePath': 'database/reports',
    'EL_Mode': 2,
    'EL_Target': '',
    'EL_MaxReportsPerScan': 150,
    'EL_Interval': '120/300',
    'EL_RequestDelay': 0.1,
    'EL_RequestTimeout': 10,
    'EL_GetModules': 0,
    'EL_GetDrivers': 0,
    'EL_GetProcesses': 0,
    'EL_UseCustomUA': 1,
    'EL_RandomUA': 1,
    'EL_LogLevel': 'INFO',
    'EL_LogConsoleOutput': 0,
    'EL_LogFile': 'ecd_logger.log',
    'EL_VerifySSL': 0,
    'EL_ShowStatsOnStart': 0,
    'GameCMS_Enable': 0,
    'GameCMS_DB_Host': 'localhost',
    'GameCMS_DB_Port': 3306,
    'GameCMS_DB_User': '',
    'GameCMS_DB_Pass': '',
    'GameCMS_DB_Name': '',
    'Telegram_Enable': 0,
    'Telegram_Token': '',
    'Telegram_ChatID': '',
    'Telegram_UseProxy': 0,
    'Telegram_Proxy': '',
    'VK_Enable': 0,
    'VK_Token': '',
    'VK_PeerID': '',
}

def load_config(filepath='config.txt'):
    cfg = DEFAULTS.copy()
    if not os.path.exists(filepath):
        return cfg

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.split('#')[0].strip()
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            if key in DEFAULTS:
                default = DEFAULTS[key]
                if isinstance(default, bool):
                    cfg[key] = value.lower() in ('1', 'true', 'yes')
                elif isinstance(default, int):
                    cfg[key] = int(value)
                elif isinstance(default, float):
                    cfg[key] = float(value)
                else:
                    cfg[key] = value

    if 'EL_Interval' in cfg:
        parts = cfg['EL_Interval'].split('/')
        cfg['min_interval'] = int(parts[0])
        cfg['max_interval'] = int(parts[1]) if len(parts) > 1 else int(parts[0])
    return cfg