````md
# Study Notes — быстрый старт (dev)

## Создание окружения и запуск (локально)
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
````

## Тесты и локальные проверки (ритуал перед PR)

```bash
# Форматирование / линтинг / импорт-организация
ruff check --fix .
black .
isort .

# Запустить тесты
pytest -q

# Прогнать pre-commit хуки на всех файлах
pre-commit run --all-files
```

## CI

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.

P01: bootstrap ready - prepared by DAT
В репозитории настроен GitHub Actions workflow **CI** (lint → tests → pre-commit).
