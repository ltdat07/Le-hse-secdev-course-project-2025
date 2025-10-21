\# BDD приёмка ключевых NFR (Gherkin)



\## Производительность списка заметок

Feature: /notes отвечает быстро на stage

&nbsp; Scenario: p95 укладывается под 200ms при 20 RPS

&nbsp;   Given сервис развернут на stage и БД заполнена 1000 заметками

&nbsp;   When выполняется 5-минутный нагрузочный тест GET /notes с 20 RPS

&nbsp;   Then p95 времени ответа ≤ 200 ms



\## Защита логина

Feature: ограничение неуспешных попыток логина

&nbsp; Scenario: превышение порога даёт 429

&nbsp;   Given у пользователя есть учётная запись

&nbsp;   When выполняют 6 неверных логинов в течение 1 минуты

&nbsp;   Then сервер отвечает 429 Too Many Requests

&nbsp;   And дальнейшие попытки временно блокируются



&nbsp; Scenario: корректный логин после окна блокировки проходит

&nbsp;   Given истекло окно блокировки

&nbsp;   When пользователь вводит верные учётные данные

&nbsp;   Then ответ 200 и выдан JWT с TTL ≤ 15 минут



\## Формат ошибок и PII

Feature: единый формат ошибок RFC7807 без утечки PII

&nbsp; Scenario: 404 по несуществующей заметке

&nbsp;   When клиент запрашивает GET /notes/999999

&nbsp;   Then ответ 404 с Content-Type application/problem+json

&nbsp;   And тело не содержит e-mail/PII

&nbsp;   And заголовок включает X-Request-ID



\## Негативные сценарии импорта

Feature: импорт Markdown ограничен по размеру

&nbsp; Scenario: превышен лимит по размеру файла

&nbsp;   When пользователь загружает файл > 5 MB

&nbsp;   Then ответ 413 Payload Too Large
