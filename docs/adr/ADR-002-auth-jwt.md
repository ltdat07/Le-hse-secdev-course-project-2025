# ADR-002 — Authentication & JWT (Argon2id)

**Status:** Accepted
**Date:** 2025-10-21
**Author:** @ltdat07
**Supersedes:** —
**Relates to:** NFR-01, NFR-02, NFR-03, R1, R11
**Component:** `auth`, `api`

---

## Context

В проекте **Study Notes** требуется безопасная авторизация пользователей и защита токенов.
Основные риски: утечка паролей, подделка JWT, брутфорс логина.
Согласно NFR и STRIDE:

- **NFR-01** — хранение паролей только с `Argon2id`;
- **NFR-02** — безопасная политика JWT (TTL ≤ 15 мин, HS256/RS256, ротация ключей);
- **NFR-03** — ограничение логина (≤5 попыток/мин/учётку);
- **STRIDE:** Spoofing (R1), Tampering (R2), Repudiation (R7), JWT Spoofing (R11).

---

## Decision

### 1. Пароли
- Хешируются через `passlib` с `Argon2id`.
- Параметры: `time_cost=3`, `memory_cost=256MB`, `parallelism=1`.
- Проверка — unit-тест, что `argon2.verify()` работает корректно.
- Пароли не логируются и не возвращаются в ответах.

### 2. JWT
- Формат: `HS256`, секрет `JWT_SECRET` из `.env`.
- TTL access-токена — **15 мин** (`JWT_TTL_SECONDS=900`).
- Payload: `sub`, `exp`, `iat`, `jti`, `iss`, `aud`.
- Подпись и валидация — библиотека `python-jose`.
- Ключи ротируются каждые ≤30 дней (`kid` в хедере).
- Refresh-токен планируется в P07.

### 3. Rate limiting
- Ограничение логина — ≤5 неуспешных попыток/минуту.
- При превышении: ответ `429 Too Many Requests`.
- После окна — попытки разрешены.
- Проверяется e2e-тестом (BDD из `NFR_BDD.md`).

### 4. Endpoints
- `POST /auth/register` — регистрация нового пользователя.
- `POST /auth/login` — выдача JWT.
- `GET /auth/me` — валидация токена, возврат данных о пользователе.

### 5. Безопасность
- Все запросы по HTTPS.
- JWT передаётся в `Authorization: Bearer ...`.
- При неверном токене — `401` с RFC7807-ошибкой.
- В логах не сохраняются `Authorization` и PII.

---

## Consequences

✅ Повышена устойчивость к:
- Брутфорсу (rate-limit);
- Утечке паролей (Argon2id);
- Подделке токенов (TTL + key rotation);
- Неконсистентным форматам ошибок (все через RFC7807).

⚙️ Увеличены требования к производительности CPU (Argon2id),
но в пределах NFR (t≈3 — допустимо для dev/stage).

---

## Links

- **NFR:**
  - [NFR-01 — Хранение паролей (Argon2id)](../security-nfr/NFR.md)
  - [NFR-02 — Политика JWT](../security-nfr/NFR.md)
  - [NFR-03 — Защита логина](../security-nfr/NFR.md)

- **Threat Model:**
  - [STRIDE — Spoofing / JWT Tampering (R1, R11)](../threat-model/STRIDE.md)

- **Next Steps:**
  - Реализация `/auth/register`, `/auth/login` и JWT utils (`src/studynotes/security.py`)
  - Добавление unit и e2e тестов
  - Проверка NFR BDD сценариев (ограничение логина, TTL токена)
