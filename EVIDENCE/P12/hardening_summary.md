# P12 - Hardening summary

- Image: studynotes:p12-10121189efba3e1a6c56e69e78d96d7136f00c0f

## Tool results
- Hadolint: 1 findings (security/hadolint.yaml)
- Checkov: passed=? failed=? skipped=? (iac/, security/checkov.yaml)
- Trivy vulns: CRITICAL=0 HIGH=1 MEDIUM=11 LOW=51 (image.tar)

## Hardening applied
- Dockerfile: non-root user, multi-stage build, no `latest`, minimal packages
- K8s: runAsNonRoot + RuntimeDefault seccomp, drop ALL caps, no privilege escalation, readonly rootfs, NetworkPolicy
- Enabled readOnlyRootFilesystem: true in container securityContext.
- SQLite needs a writable path, so we mount a writable volume at /data and set DATABASE_URL=sqlite:////data/app.db (see iac/k8s.yaml).

