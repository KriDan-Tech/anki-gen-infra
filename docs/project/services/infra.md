# infra

## Владение и эксплуатационные контексты
Сборка локального polyrepo: compose, Postgres, RabbitMQ, volumes, reverse proxy, automation/ACME и VM-only tooling. Соседние contexts (infra, ansible, proxy) имеют свои operating boundary; документация запуска — в `infra/README.md`.

## Наблюдаемая реализация (2026-11-18)
`infra/.env.example` содержит общий SMTP contract; default `infra/docker-compose.yml` передаёт значения Keycloak для ручного compare, но realm JSON остаётся baked-in из `auth-keycloak/Dockerfile`. Для first import доступен `auth-keycloak/provision-smtp.py --prepare-import` и отдельный необязательный `infra/docker-compose.smtp-import.yml`: оператор явно готовит protected runtime export и передаёт overlay в Compose. Bind скрывает baked-in import directory только в таком запуске; default dev flow и Ansible automation не затронуты. Генерация не вызывает Keycloak Admin/SMTP и не отправляет тестовое письмо; существующий realm повторным импортом не обновляется. Runtime/deployed config не проверялся. `--check` по-прежнему аутентифицируется и читает realm; возможны session/audit side effects, конфигурация и доставка не меняются. Явный `--apply` использует kcadm из выбранного Compose service и не меняет Compose или Ansible defaults.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `infra/docker-compose.yml`, README, proxy/Ansible/ACME assets (2026-11-16). Локальная ветка `feat/source-durable-progress-2026-11-16` @ed686b5; untracked служебные .serena не включены. Checked-in compose/Ansible — описание желаемой конфигурации, не доказательство того, что deployed. Версии контейнеров закреплены в самих manifests; не выводить operational state из тега образа.

## Утверждённая цель
Инфраструктура обеспечивает backend dependencies и изолированный путь проверки; дальнейшие runtime checks выполняются только на docker-vm. Отдельно учитывать локальные и production credentials/volumes, не переносить секреты в docs.

## Разрывы и неизвестное
Эта документационная задача не выполняла runtime actions. Deployment, DNS, firewall, сертификат, реальные volumes и точные production versions остаются неизвестны; не запускать изменения операционной среды.

## Практическая навигация (осмотр 2026-11-16)
[infra/docker-compose.yml](../../infra/docker-compose.yml) определяет local assembled services, build contexts, networks, volumes и environment wiring; [infra/.env.example](../../infra/.env.example) перечисляет config names/sample placeholders, но не реальные секреты. Reverse proxy, ACME и deployment automation находятся в `infra/` и `infra/ansible/`; checked-in configuration не тождественна deployed environment.

Поддерживающий вход: [README](../../infra/README.md), [Compose](../../infra/docker-compose.yml), [Postgres initialization context](../../infra/postgres/README.md), [vNext full-stack handoff](../../infra/docs/task043-vnext-fullstack-handoff.md). При изменении wiring сверять соответствующие service build contexts и deployment-specific role; в рамках этого справочника никаких операций с окружением не выполнялось.

## Task065 — notification wiring, source-only 2026-11-19

Источники: `infra/docker-compose.yml`, `.env.example`,
`ansible/roles/app/{defaults/main.yml,tasks/preparation.yml,tasks/docker.yml}`,
`postgres/init/01-databases.sh`.
app_repos включает remote `git@github.com:KriDan-Tech/anki-gen-notification.git`;
Compose context ровно `./anki-gen-notification`. Git clone на controller
become:false, optional per-repo key_file также controller-side, затем synchronize
в /srv/myapp. Target SSH identity не доказывает доступ controller к private remote.

Уточнение владельца 2026-11-19: выбран чистый запуск стенда с нуля.
Базу `notification_sandbox_db` и роль создаёт тот же create_service_db в общем
postgres/init/01-databases.sh, что остальные service DBs, только при пустом
postgres-data. Отдельные notification DB script/mount и два предварительных
PostgreSQL-start/DB-provision tasks Ansible удалены; обычный build/start и proxy
restart сохранены. Existing volumes автоматически не дополняются и не очищаются.
Known deployed deck V1 mismatch остаётся историческим caveat для reuse старой БД,
а не требованием repair при чистом запуске; Flyway repair не добавлен.
Internal notification без public send API/port, dedicated directory secret и shared
SMTP7 contract. Keycloak не startup/health dependency: outage откладывает jobs
с bounded retries, не мешает wait. External SMTP требует TLS, all-empty settings
явно выбирают internal Mailpit.

RabbitMQ named data volume и stable hostname добавлены для durable queues при recreation;
для существующего broker переход с container-local storage требует отдельной
operator migration оценки до rollout (новый volume скрывает старые данные).
Postgres17/RabbitMQ4 — major tags, не exact patches.
Ни runtime, ни deployment, ни provisioning/send не выполнялись.

## CPU source-service — решение 2026-11-19

Источник: `infra/docker-compose.yml`. По решению владельца лимит `cpus`
у source-service удалён; переменная `SOURCE_CPU_BUDGET` больше не используется.
Сервис разделяет доступный CPU Docker-хоста с остальными контейнерами без собственной
CPU-квоты. Настройки потоков OCR не менялись. Ansible копирует общий Compose-файл.
Статическая правка; повторный запуск/deployment не выполнялся.

## SMTP selected-instance recovery — source-only 2026-11-19

`auth-keycloak/provision-smtp.py` разрешает HTTP из selected Compose keycloak
published8080 того же project/env/compose context, что kcadm exec. Требуются один
running instance, один loopback binding (127.0.0.1 или [::1]) и local Unix-socket
Docker daemon. Fixed8180 fallback отсутствует; текущий infra binding
127.0.0.1:8180:8080 совместим без изменения Compose/Ansible defaults.
Relative paths project-relative; inherited SMTP interpolation сохраняется.
Nonempty DOCKER_HOST + DOCKER_CONTEXT одновременно запрещены до Compose/auth;
разрешён каждый отдельно (local Unix socket) либо verified current local context.
Version proof — selected container kc.sh --version, не privileged REST serverinfo.

JWT role gate удалён: actual intended update авторизует Keycloak server.
Short-token fences, ordinary full GET-merge-PUT, full nonSMTP comparison и
postlaunch uncertainty сохранены. Opt-in integration source создаёт только свои
unique projects/volumes и fake SMTP, не использует production .env/credentials,
не вызывает send endpoints, проверяет private stored password и scoped cleanup.
На docker-vm Python3.12.3 все38 focused regressions прошли;4 protected-filesystem
cases skipped из-за отсутствия root/sudo.13 integration cases не запускались
(root требуется); Docker29.9.3/Compose5.7.0 подтверждены. Image digest и runtime/
integration-cleanup outcomes пока неизвестны.
[API evidence и permitted-executor handoff](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/docs/smtp-api-verification.md).
