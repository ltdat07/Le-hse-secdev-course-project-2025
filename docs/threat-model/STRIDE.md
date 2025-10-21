# STRIDE — ключевые угрозы по потокам/элементам

| Поток/Элемент | Угроза (STRIDE)                              | РискID | Контроль/мера                                          | NFR                          | Проверка/Артефакт         |
|---------------|----------------------------------------------|--------|--------------------------------------------------------|------------------------------|---------------------------|
| F1 /login     | Spoofing (кража пароля)                      |   R1   | Argon2id, rate-limit 5/мин, 429, аудит логов           | NFR-01, NFR-03               | e2e + нагрузочный тест    |
| F1 /login     | Tampering (подмена тела запроса)             |   R2   | Pydantic-валидация, только HTTPS                       | NFR-06                       | контракт-тест             |
| F2 /notes     | Information Disclosure (PII в ответах/логах) |   R3   | Маскирование PII, RFC7807, X-Request-ID                | NFR-04, NFR-06               | контракт-тест             |
| F2 /notes     | DoS (массовые запросы)                       |   R4   | Rate-limit по IP/JWT, пагинация, timeout 3s            | NFR-11, NFR-03               | интеграционный тест       |
| F3 import     | Tampering (вредный Markdown/HTML)            |   R5   | Лимит размера, санитизация Markdown, deny HTML         | NFR-09, NFR-06               | e2e импорт                |
| F6 export     | Info Disclosure (экспорт чужих заметок)      |   R6   | Owner-only ACL, проверка JWT/owner                     | NFR-02, NFR-08               | unit ACL                  |
| AUTH          | Repudiation (отказ от действий)              |   R7   | Correlation-ID, audit trail                            | NFR-04                       | проверка логов            |
| DB            | Elevation of Privilege                       |   R8   | Least-privilege, сервисный юзер с минимальными правами | NFR-12                       | ревью конфигураций        |
| Logs          | Information Disclosure                       |   R9   | Не логировать PII/секреты                              | NFR-04                       | линт логов                |
| Backups       | Disclosure                                   |   R10  | Шифрование бэкапов, ограниченный доступ                | NFR-12                       | политика/чек-лист         |
| JWT           | Spoofing (подделка токена)                   |   R11  | TTL ≤ 15m, RS256/HS256, ротация ключей                 | NFR-02                       | unit JWT                  |
| API           | Tampering (методы/статусы/контракты)         |   R12  | Контракт-тесты, строгие статус-коды                    | NFR-06                       | tests                     |
