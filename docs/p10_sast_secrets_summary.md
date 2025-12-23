# P10 — SAST & Secrets summary

Этот summary дополняется/обновляется при изменениях правил Semgrep/Gitleaks или при появлении findings.
Актуальные отчёты для каждого запуска лежат в артефакте CI `P10_EVIDENCE` (Semgrep SARIF + Gitleaks JSON + summary).

## How we use these results дальше
- В PR смотрим summary и при необходимости заводим Issue/фикс.
- План: подключить SARIF в GitHub Code Scanning (потребуется `security-events: write`).