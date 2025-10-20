\# ADR-001: RFC7807 Error Handling

Дата: 2025-10-20

Статус: Accepted



\## Context

До внедрения этого решения сервис возвращал ошибки в произвольном формате (`{"detail": "Not Found"}`),

что мешало трассировке, тестированию и интеграции с другими сервисами.

Также отсутствовал `correlation\_id`, из-за чего логи не связывались с запросами.



\## Decision

Реализован централизованный обработчик ошибок по стандарту \*\*\[RFC 7807 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc7807)\*\*.

Введён единый JSON-контракт для всех ошибок:



```json

{

&nbsp; "type": "about:blank",

&nbsp; "title": "Validation error",

&nbsp; "status": 422,

&nbsp; "detail": "...",

&nbsp; "correlation\_id": "uuid",

&nbsp; "code": "VALIDATION\_ERROR",

&nbsp; "message": "...",

&nbsp; "details": {}

}
