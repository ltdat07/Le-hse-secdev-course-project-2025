\# ADR-002 — Authentication \& JWT (Argon2id)



\*\*Status:\*\* Accepted

\*\*Date:\*\* 2025-10-21

\*\*Author:\*\* @ltdat07

\*\*Supersedes:\*\* —

\*\*Relates to:\*\* NFR-01, NFR-02, NFR-03, R1, R11

\*\*Component:\*\* `auth`, `api`



---



\## Context



В проекте \*\*Study Notes\*\* требуется безопасная авторизация пользователей и защита токенов.

Основные риски: утечка паролей, подделка JWT, брутфорс логина.

Согласно NFR и STRIDE:



\* \*\*NFR-01\*\* — хранение паролей только с `Argon2id`;

\* \*\*NFR-02\*\* — безопасная политика JWT (TTL ≤ 15 мин, HS256/RS256, ротация ключей);

\* \*\*NFR-03\*\* — ограничение логина (≤5 попыток/мин/учётку);

\* \*\*STRIDE:\*\* Spoofing (R1), Tampering (R2), Repudiation (R7), JWT Spoofing (R11).



---



\## Decision



1\. \*\*Пароли\*\*

&nbsp;  - Хешируются через `passlib` с `Argon2id`.

&nbsp;  - Параметры: `time\_cost=3`, `memory\_cost=256MB`, `parallelism=1`.

&nbsp;  - Проверка — unit-тест, что `argon2.verify()` работает корректно.

&nbsp;  - Пароли не логируются, не возвращаются в ответах.



2\. \*\*JWT\*\*

&nbsp;  - Формат: `HS256`, секрет `JWT\_SECRET` из `.env`.

&nbsp;  - TTL access-токена — \*\*15 мин\*\* (`JWT\_TTL\_SECONDS=900`).

&nbsp;  - Payload: `sub` (user\_id), `exp`, `iat`, `jti`, `iss`, `aud`.

&nbsp;  - Подпись и валидация — библиотека `python-jose`.

&nbsp;  - Ключи ротируются каждые ≤30 дней (`kid` в хедере).

&nbsp;  - Refresh-токен планируется в P07.



3\. \*\*Rate limiting\*\*

&nbsp;  - Ограничение логина — ≤5 неуспешных попыток/минуту.

&nbsp;  - При превышении: ответ `429 Too Many Requests`.

&nbsp;  - После окна — попытки разрешены.

&nbsp;  - Проверяется e2e-тестом (BDD из `NFR\_BDD.md`).



4\. \*\*Endpoints\*\*

&nbsp;  - `POST /auth/register` — регистрация нового пользователя.

&nbsp;  - `POST /auth/login` — выдача JWT.

&nbsp;  - `GET /auth/me` — валидация токена, возврат данных о пользователе.



5\. \*\*Безопасность\*\*

&nbsp;  - Все запросы по HTTPS.

&nbsp;  - JWT передаётся в `Authorization: Bearer ...`.

&nbsp;  - При неверном токене — `401` с RFC7807-ошибкой.

&nbsp;  - В логах не сохраняются `Authorization` и PII.



---



\## Consequences



✅ Повышена устойчивость к:

\- Брутфорсу (rate-limit);

\- Утечке паролей (Argon2id);

\- Подделке токенов (TTL + key rotation);

\- Неконсистентным форматам ошибок (все через RFC7807).



⚙️ Увеличены требования к производительности CPU (Argon2id),

но в пределах NFR (t≈3 — допустимо для dev/stage).



---



\## Links



\* \*\*NFR:\*\*

&nbsp; - \[NFR-01 — Хранение паролей (Argon2id)](../NFR.md)

&nbsp; - \[NFR-02 — Политика JWT](../NFR.md)

&nbsp; - \[NFR-03 — Защита логина](../NFR.md)



\* \*\*Threat Model:\*\*

&nbsp; - \[STRIDE — Spoofing / JWT Tampering (R1, R11)](../threat-model/STRIDE.md)



\* \*\*Next Steps:\*\*

&nbsp; - Реализация `/auth/register`, `/auth/login` и JWT utils (`src/studynotes/security.py`)

&nbsp; - Добавление unit и e2e тестов

&nbsp; - Проверка NFR BDD сценариев (ограничение логина, TTL токена)



---
