# infra

## Владение и эксплуатационные контексты
Сборка локального polyrepo: compose, Postgres, RabbitMQ, volumes, reverse proxy, automation/ACME и VM-only tooling. Соседние contexts (infra, ansible, proxy) имеют свои operating boundary; документация запуска — в `infra/README.md`.

## Наблюдаемая реализация (2026-11-18)
`infra/.env.example` содержит placeholder-only общий SMTP контракт (`SMTP_HOST`, `SMTP_PORT`, `SMTP_TLS_MODE`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_FROM_NAME`); compose передаёт его Keycloak для ручного compare. Future notification worker пока не wired. Это не автоматическое обновление realm и не доказательство deployed SMTP. `--check` аутентифицируется и читает realm; возможны session/audit side effects, но конфигурация и доставка не меняются.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `infra/docker-compose.yml`, README, proxy/Ansible/ACME assets (2026-11-16). Локальная ветка `feat/source-durable-progress-2026-11-16` @ed686b5; untracked служебные .serena не включены. Checked-in compose/Ansible — описание желаемой конфигурации, не доказательство того, что deployed. Версии контейнеров закреплены в самих manifests; не выводить operational state из тега образа.

## Утверждённая цель
Инфраструктура обеспечивает backend dependencies и изолированный путь проверки; дальнейшие runtime checks выполняются только на docker-vm. Отдельно учитывать локальные и production credentials/volumes, не переносить секреты в docs.

## Разрывы и неизвестное
Эта документационная задача не выполняла runtime actions. Deployment, DNS, firewall, сертификат, реальные volumes и точные production versions остаются неизвестны; не запускать изменения операционной среды.

## Практическая навигация (осмотр 2026-11-16)
[infra/docker-compose.yml](../../infra/docker-compose.yml) определяет local assembled services, build contexts, networks, volumes и environment wiring; [infra/.env.example](../../infra/.env.example) перечисляет config names/sample placeholders, но не реальные секреты. Reverse proxy, ACME и deployment automation находятся в `infra/` и `infra/ansible/`; checked-in configuration не тождественна deployed environment.

Поддерживающий вход: [README](../../infra/README.md), [Compose](../../infra/docker-compose.yml), [Postgres initialization context](../../infra/postgres/README.md), [vNext full-stack handoff](../../infra/docs/task043-vnext-fullstack-handoff.md). При изменении wiring сверять соответствующие service build contexts и deployment-specific role; в рамках этого справочника никаких операций с окружением не выполнялось.
