# 🛡️ ECD Logger

<p align="center">
  <img src="https://img.shields.io/badge/version-1.4.3-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-green?style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/badge/license-GPL%203.0-red?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux-lightgrey?style=for-the-badge" alt="Platform">
</p>

**ECD Logger** — это автоматизированная система мониторинга античит-отчётов **Easy Cheat Detector** (CS 1.6 и другие игры).  
Программа в реальном времени собирает данные с `fungun.net`, фильтрует по серверам, сохраняет в SQLite, подгружает детали нарушителя (драйверы, модули, процессы), интегрируется с **GameCMS** и отправляет уведомления в **Telegram** и **VK**.

## 📦 Возможности

- 🔍 **Мониторинг ECD** – пагинированный сбор всех отчётов (не только первых 50–150)
- 🎯 **3 режима фильтрации** – только целевой сервер, все сервера, целевой + скрытые (`-` / `N/A`)
- 💾 **Локальное хранение** – SQLite с расширенной схемой (основные отчёты + драйверы, модули, процессы)
- 🧩 **Детальный анализ** – выгрузка архива: драйверы, модули, процессы нарушителя
- 🎮 **Интеграция с GameCMS** – мониторинг таблицы `ecd_logs` в MySQL (новые записи, смена статуса)
- 📨 **Уведомления** – встроенная поддержка Telegram (с прокси) и VK API
- 🕵️ **Маскировка** – случайный User-Agent из списка >200 современных браузеров
- 🛡 **Защита от блокировок** – задержки, повторные попытки, обработка 403 с откладыванием отчётов
- ⚙️ **Гибкий конфиг** – все настройки в одном файле `config.txt`
- 📊 **Статистика** – количество отчётов по статусам, за последние 7 дней
- 🚀 **Автоустановка зависимостей** – скрипт `setup.py` установит всё необходимое

## 📋 Требования

- Python **3.8+**
- pip (менеджер пакетов)
- Доступ в интернет (для запросов к `fungun.net`)
- MySQL (только при включённой интеграции с GameCMS)

## 🚀 Установка и запуск
### 1. Клонируйте репозитирий
```bash
git clone https://github.com/yourusername/ecd-logger.git
cd ecd-logger
```

### 2. (Опционально) Создайте виртуальное окружение
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. Установите зависимости (автоматически или вручную)
```bash
python setup.py            # автоустановка недостающих пакетов
# или вручную:
pip install -r requirements.txt   # если есть requirements.txt
```

### 4. Настройте конфиг: config.txt

### 5. Запустите программу
```bash
python app.py
```

## 📄 Лицензия
Данное программное обеспечение распространяется под лицензией **GNU General Public License v3.0**
Подробнее см. в файле [LICENSE](https://github.com/ваш_username/ecd-logger/blob/main/LICENSE)

## 📬 Поддержка
По вопросам багов, предложений и помощи пишите в Issues данного репозитория.
Автор не несёт ответственности за возможные блокировки IP со стороны fungun.net — используйте разумные интервалы запросов.

<p align="center"> <sub>Written using Python by Kraken ABT</sub> </p>
