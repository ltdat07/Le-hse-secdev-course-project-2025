# Study Notes — быстрый старт

## Создание окружения и запуск 
```bash
# Создать виртуальное окружение
python -m venv .venv

# Активировать виртуальное окружение
# Linux / macOS:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Установить зависимости
pip install -r requirements.txt -r requirements-dev.txt

# Установить git hooks
pre-commit install

# Запустить приложение (dev)
uvicorn app.main:app --reload
