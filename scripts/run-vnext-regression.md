# Low-token vNext regressions (VM only)

Use Python 3.12+ on **docker-vm** (hostname `external-docker`), not the workstation.
Copy this script and desired dirty source trees to the VM first, preserving
local changes. All arguments below are **VM paths**; choose a never-used run directory.

```sh
ssh docker-vm 'python3 /home/docker-agent/run-vnext-regression.py \
  --source /home/docker-agent/work/vnext-regression-20261113-10615/source-service \
  --extractor /home/docker-agent/work/vnext-regression-20261113-10615/vocab-extractor \
  --frontend /home/docker-agent/work/vnext-regression-20261113-10615/web-frontend \
  --run-dir /home/docker-agent/work/vnext-preset-UNIQUE \
  --node-modules /home/docker-agent/work/vnext-regression-20261113-10615/web-frontend/node_modules'
```

Only lanes: Python pytest, frontend npm test, and extractor isolated Maven verify.
No optional OCR/HTTP benchmarks, Compose, deployment, provider requests, commits
or pushes. All three are attempted even after failure.

Prerequisites: installed Docker images `task043-v2-test:latest`,
`node:24-bookworm-slim`, `maven:3.9-eclipse-temurin-21`, `postgres:17`,
`rabbitmq:4-management`; VM-supplied compatible frontend node_modules; a warm
Maven cache (default `~/.cache/anki-regression-m2`). No npm installation or image
pull is performed. Maven may fetch missing public dependencies using the existing
Java wrapper; no host service credentials/config are inherited.

Options: `--python-image`, `--frontend-image`, `--node-modules`, `--maven-cache`,
`--suite-timeout SECONDS` (per suite command, default 1800). If the known VM's
hostname changes, pin its independently verified `/etc/machine-id` with
`--vm-machine-id`; there is no unrestricted local bypass.

Four output lines: status/counts/duration/private log per suite, then overall
status and `summary.json`. Exit 0 means all passed; 1 means any suite failed
(including missing/zero reports); 2 means invalid setup. Inspect only a failed
suite's log as needed, not all successful logs.

The fresh private run directory retains sanitized snapshots, per-file SHA256/Git
SHA provenance, resolved image IDs, logs, reports and fresh Java build artifacts.
Git SHA may be unavailable for exported trees; file hashes still apply. Excluded:
Git metadata, `.env*`, private/credential files, environments, node_modules,
targets, build outputs and caches. Source symlinks are omitted; dependency-relative
symlinks are preserved, external dependency links omitted. Dependencies are copied
separately after provenance hashing and are not independently content-hashed.

Python uses a read-only snapshot/root and no network, writing JUnit into reports.
Frontend runs `npm test -- --watch=false` on a writable disposable snapshot with
no network and parses the completed Vitest summary. Java stages path/cache and
unique-container-name adaptations of `scripts/test-usage-isolated.sh`, leaving
the original input untouched. Its disposable PostgreSQL/RabbitMQ network and
Maven behavior are otherwise unchanged. Reports come only from this run's fresh
mktemp target, never input target XML. Do not supply caches with credentials
(`settings.xml` is rejected). Avoid simultaneous runs sharing a cache if its
toolchain cannot coordinate writes. Cleanup records removal return codes and
bounded daemon-side resource listings in summary.json; already-absent resources
are tolerated only after verified absence. Remaining resources or an inability
to verify absence fail the suite, including after a command timeout.
