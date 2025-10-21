# ADR-001: RFC7807 Error Handling

**Дата:** 2025-10-20
**Статус:** Accepted

## Context

До внедрения этого решения сервис возвращал ошибки в произвольном формате (`{"detail": "Not Found"}`),
что мешало трассировке, тестированию и интеграции с другими сервисами.
Также отсутствовал `correlation_id`, из-за чего логи не связывались с запросами.

## Decision

Реализован централизованный обработчик ошибок по стандарту **[RFC 7807 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc7807)**.
Введён единый JSON-контракт для всех ошибок:

```json
{
  "type": "about:blank",
  "title": "Validation error",
  "status": 422,
  "detail": "...",
  "correlation_id": "uuid",
  "code": "VALIDATION_ERROR",
  "message": "...",
  "details": {}
}
```
