import sys
import subprocess

REQUIRED = [
    "requests",
    "beautifulsoup4",
    "urllib3",
    "mysql-connector-python"
]

def install_package(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def main():
    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Устанавливаем недостающие пакеты: {', '.join(missing)}")
        for pkg in missing:
            install_package(pkg)
        print("Готово!")
    else:
        print("Все зависимости уже установлены.")

if __name__ == "__main__":
    main()