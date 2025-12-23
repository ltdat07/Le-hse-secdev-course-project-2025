# P12 - Hardening summary

- Image: studynotes:p12-835972854ab81e7d9ed78ff2b20f652efa4b8260

## Tool results
- Hadolint: 1 findings (security/hadolint.yaml)
- Checkov: passed=88 failed=1 skipped=0 (iac/, security/checkov.yaml)
- Trivy vulns: CRITICAL=0 HIGH=1 MEDIUM=11 LOW=51 (image.tar)

## Hardening applied
- Dockerfile: non-root user, multi-stage build, no `latest`, minimal packages
- K8s: runAsNonRoot + RuntimeDefault seccomp, drop ALL caps, no privilege escalation, readonly rootfs, NetworkPolicy
- Enabled readOnlyRootFilesystem: true in container securityContext.
- SQLite needs a writable path, so we mount a writable volume at /data and set DATABASE_URL=sqlite:////data/app.db (see iac/k8s.yaml).

