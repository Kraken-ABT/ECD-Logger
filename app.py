import sys
import time
import threading
import logging
from modules.config import load_config
from modules.database_sqlite import ReportsDB
from modules.monitor_ecd import ECDMonitor
from modules.monitor_gamecms import GameCMSMonitor
from modules.notifications import get_notifier
import setup

setup.main()

def setup_logging(cfg):
    level = getattr(logging, cfg.get('EL_LogLevel', 'INFO'), logging.INFO)
    handlers = [logging.FileHandler(cfg.get('EL_LogFile', 'ecd_logger.log'), encoding='utf-8')]
    if cfg.get('EL_LogConsoleOutput', 0):
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)

def main():
    cfg = load_config()
    logger = setup_logging(cfg)
    logger.info("ECD Logger запущен. Режим: %s", "GameCMS + FunGun" if cfg.get('GameCMS_Enable') else "FunGun only")

    notifier = get_notifier(cfg)
    db = ReportsDB(cfg['EL_DataBasePath'])

    monitor_ecd = ECDMonitor(cfg, db, notifier)
    thread_ecd = threading.Thread(target=monitor_ecd.run, daemon=True, name="FunGunScanner")
    thread_ecd.start()

    if cfg.get('GameCMS_Enable'):
        monitor_gamecms = GameCMSMonitor(cfg, db, notifier)
        monitor_gamecms.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Остановка по требованию пользователя")
        print("\nРабота завершена.")


if __name__ == "__main__":
    main()