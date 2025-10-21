\# ADR-003 — Secrets \& Config (ENV)



\*\*Status:\*\* Accepted

\*\*Date:\*\* 2025-10-21

\*\*Relates to:\*\* NFR-12, NFR-04, R9, R10

\*\*Component:\*\* platform, auth



\## Context

Секреты и ключи (напр., JWT) не должны храниться в коде/репозитории. Нужна единая стратегия конфигурации и ротации.



\## Decision

\- Конфигурация через переменные окружения; локально допускается `.env`.

\- Пример — `.env.example` (без чувствительных значений).

\- `JWT\_SECRET` читается из ENV; хардкода в коде нет.

\- Ротация секрета ≤ 30 дней; `kid` в JWT-хедере зарезервирован.

\- PII/секреты не логируем; `.env` в `.gitignore`.



\## Alternatives

\- Хардкод в файлах — риск утечек, не проходит ревью.

\- KMS/Vault — безопаснее, но избыточно для MVP; в план на будущие практики.



\## Security impact

\+ Снижается риск утечки секретов (VCS/логи/бэкапы).

– Требуется дисциплина управления ENV на стендах.



\## Rollout plan

1\) `.env.example` уже в репо; `.env` — в `.gitignore`.

2\) В `security.py` читать `JWT\_SECRET` из ENV.

3\) Проверка: linters, code review, CI.



\## Links

\- NFR-12 (ротация секретов), NFR-04 (PII \& correlation\_id)

\- Risks: R9 (утечка в логах), R10 (утечка бэкапов)

\- Код: `src/studynotes/security.py`

\- Тест: `tests/test\_security\_argon2.py`
