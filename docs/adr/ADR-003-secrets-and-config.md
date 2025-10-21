# ADR-003 — Secrets & Config (ENV)

**Status:** Accepted
**Date:** 2025-10-21
**Relates to:** NFR-12, NFR-04, R9, R10
**Component:** platform, auth

## Context

Секреты и ключи (например, JWT) не должны храниться в коде или репозитории.
Нужна единая стратегия конфигурации и ротации.

## Decision

- Конфигурация через переменные окружения; локально допускается `.env`.
- Пример — `.env.example` (без чувствительных значений).
- `JWT_SECRET` читается из ENV; хардкода в коде нет.
- Ротация секрета ≤30 дней; `kid` в JWT-хедере зарезервирован.
- PII/секреты не логируются; `.env` добавлен в `.gitignore`.

## Alternatives

- Хардкод в файлах — риск утечек, не проходит ревью.
- KMS/Vault — безопаснее, но избыточно для MVP; в план на будущие практики.

## Security impact

+ Снижается риск утечки секретов (VCS, логи, бэкапы).
– Требуется дисциплина управления ENV на стендах.

## Rollout plan

1. `.env.example` уже в репозитории; `.env` — в `.gitignore`.
2. В `security.py` читать `JWT_SECRET` из ENV.
3. Проверка: линтеры, code review, CI.

## Links

- NFR-12 (ротация секретов), NFR-04 (PII & correlation_id)
- Risks: R9 (утечка в логах), R10 (утечка бэкапов)
- Код: `src/studynotes/security.py`
- Тест: `tests/test_security_argon2.py`
