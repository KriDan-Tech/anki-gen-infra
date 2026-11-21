# infra

> Каноническая polyrepo-документация: [docs/index](https://github.com/KriDan-Tech/anki-gen-infra/blob/main/docs/project/README.md) · [infra — ответственность, target и gaps](https://github.com/KriDan-Tech/anki-gen-infra/blob/main/docs/project/services/infra.md). Опубликованное зеркало поддерживается в infra; source-of-truth реализации — исходники этого сервиса.

Инфраструктура и запуск всего проекта dev-anki-gen. Своего кода здесь нет — только
`docker-compose.yml`, init-скрипты Postgres и переменные окружения (полирепо, см. STRUCTURE.md).
Сервисы собираются из соседних репозиториев через `build.context: ../<сервис>`.

## Что поднимается (этапы 1–6)

| Контейнер | Образ | Порты (dev) | Назначение |
|---|---|---|---|
| postgres | `postgres:17` | 5432 | Один сервер, отдельная база на сервис |
| rabbitmq | `rabbitmq:4-management` | 5672, 15672 | Брокер событий + management UI |
| mailpit | `axllent/mailpit` | 8025, 1025 | Заглушка SMTP для Keycloak (письма подтверждения и сброса) |
| keycloak | build `../auth-keycloak` (`quay.io/keycloak/keycloak:26.8.1`) | 8180 | Вход, регистрация, realm `anki-gen` (этап 6) |
| api-gateway | build `../api-gateway` | 8080 | Единая точка входа, JWT, Swagger UI (этап 6) |
| source-service | build `../source-service` | — (внутри сети, 8081) | Приём PDF (Python, этап 3) |
| vocab-extractor | build `../vocab-extractor` | — (внутри сети, 8082) | Извлечение слов |
| card-builder | build `../card-builder` | — (внутри сети, 8083) | Сборка карточек |
| deck-service | build `../deck-service` | — (внутри сети, 8084) | Колоды, экспорт `.apkg` |
| billing-service | build `../billing-service` | — (внутри сети) | Платежный sandbox ledger в отдельной базе общего PostgreSQL |
| acme | `goacme/lego:v5.5.2` | — | разовый запуск: выпуск/продление LE |
| node-exporter / cAdvisor / NGINX exporters | pinned tags in Compose | 9100 / 8088 / 9113 / 4040 (loopback-safe) | private metrics targets |
| Spring Actuator | six host ports 19090–19095 | 9090 in Java containers; notification remains on 8086 for its health probe | Prometheus scrape (`/actuator/prometheus`) |

Публичный application ingress остаётся только через gateway (8080), Keycloak (8180) и Mailpit (8025); порты сервисов (8081–8084) не публикуются. Отдельно Compose публикует Actuator на host-портах 19090–19095 на всех IPv4-интерфейсах для удалённого Prometheus. NAT/firewall нужно настроить так, чтобы эти порты принимали соединения только от metrics-хоста. Postgres и RabbitMQ пока доступны с хоста (см. открытые вопросы в отчёте этапа 6).
**Redis не используется.** `audio-service` — вне MVP.

## Наблюдаемость (source-only)

Observability manifests are source-controlled in `docs/OBSERVABILITY.md` and
`ansible/roles/prometheus_grafana`; they are **not deployed/runtime-verified**.
Exporter and Grafana/Prometheus binds default to loopback; there are no public
metrics routes. Private/VPN binds, inventory targets, routing and firewall allow
rules must be configured by the operator; no addresses or ACLs are assumed.
The optional source-service `/metrics` target is configurable and disabled by
default. Grafana file-provisioned dashboards/rules may be overwritten on
provisioning/redeploy; configure a contact point and notification policy once in
UI if notifications are required. Manual dashboard import: Dashboards → New →
Import → `ansible/roles/prometheus_grafana/files/dashboards/infra-overview.json`.
The nginx-log exporter v1.11.0 HCL shape and `-config-file` flag are verified
against exact-version upstream sources; parser behavior and bounded access-log
rotation remain unverified/unimplemented. See docs/OBSERVABILITY.md. No deployment
was run.

## Запуск

```bash
cp .env.example .env         # заполнить пароли и (для этапов 2+) ИИ-ключи
chmod 600 .env
docker compose up -d --build
```

- Swagger UI всех сервисов (через gateway): http://localhost:8080/swagger-ui.html
- Вход в Swagger: кнопка Authorize → клиент `swagger` в Keycloak
- Keycloak (админка и OIDC): http://localhost:8180 (логин из `KEYCLOAK_ADMIN_*`)
- RabbitMQ UI: http://localhost:15672 (логин/пароль из `RABBITMQ_DEFAULT_*`)
- Mailpit UI (письма Keycloak): http://localhost:8025
- Realm `anki-gen`: импорт из `auth-keycloak/realm-export.json` идёт только при первом создании realm;
  подробнее — `auth-keycloak/README.md`. Google: заполнить `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
  в `.env` (пока пустые — вход через Google не работает).
- Для provisioning-клиента billing-admin Compose-файл в checkout укажите явно:
  `--project-directory /path/to/dev-anki-gen --compose-file infra/docker-compose.yml`.
  На целевом сервере по умолчанию используется `/srv/myapp/docker-compose.yml`.

## SMTP first-import (opt-in)

Default Compose и Ansible сохраняют исходный flow: Keycloak image импортирует baked-in
auth-keycloak/realm-export.json только при первом создании realm. Для opt-in first import
скрипт auth-keycloak/provision-smtp.py готовит защищённый runtime export, а отдельный
infra/docker-compose.smtp-import.yml монтирует его поверх /opt/keycloak/data/import.
Ни один из файлов не включается автоматически. Точные команды для checkout и /srv/myapp,
правила ownership, Mailpit fallback, idempotency, неизменность существующего realm и
непроверенная registration UI sequence описаны в auth-keycloak/README.md.

Подготовить runtime export можно из checkout; это не является поддерживаемым Compose startup,
поскольку build contexts требуют развёрнутую структуру `/srv/myapp`. После подготовки передайте
каталог `infra/keycloak-import/` на сервер в `/srv/myapp/keycloak-import/`.

~~~bash
cd /home/srvadmin/projects/dev-anki-gen
sudo install -d -o root -g 0 -m 0750 infra/keycloak-import
sudo python3 auth-keycloak/provision-smtp.py \
  --prepare-import --project-directory "$PWD" \
  --compose-file infra/docker-compose.yml --env-file infra/.env \
  --output-directory "$PWD/infra/keycloak-import"
~~~

На сервере после доставки подготовленного каталога, Compose override и остальных build contexts
в `/srv/myapp`, startup запускается в развёрнутой структуре (и последующие Compose up, пока нужен
mount, также должны передавать оба Compose файла и эту переменную):

~~~bash
cd /srv/myapp
KEYCLOAK_IMPORT_DIRECTORY=/srv/myapp/keycloak-import docker compose \
  -f /srv/myapp/docker-compose.yml \
  -f /srv/myapp/docker-compose.smtp-import.yml \
  up -d keycloak
~~~

Первый импорт не меняет существующий realm; для повторного импорта рассматривайте только
отдельную базу keycloak_db и её backup/recovery-процедуру. Не удаляйте shared PostgreSQL
volume и не используйте docker compose down -v. Подготовка не вызывает SMTP и не отправляет
письмо. Runtime/deployed состояние здесь не проверялось.

## HTTPS и сертификат (TLS_MODE)

Вход — `https://PUBLIC_HOST/` через proxy (443; 80 → 301). Nginx читает активную пару `certs/tls.crt` + `certs/tls.key`.

- **`selfsigned`** (по умолчанию, `TLS_MODE=selfsigned`): самоподписанный, для IP и localhost. Ansible выпускает его в `certs/selfsigned/` и копирует в активную пару. `tls.crt` забирается в `infra/certs/<host>.crt` — его можно добавить в доверенные на устройствах.
- **`letsencrypt`** (`TLS_MODE=letsencrypt`): сертификат Let's Encrypt через DNS-01 (TXT-запись в зоне Selectel), входящий 80 не нужен. Только для домена, не для IP и localhost. Режим означает согласие с Subscriber Agreement Let's Encrypt.
  1. Создать в Selectel сервисного пользователя с ролью на проект, где лежит DNS-зона `PUBLIC_HOST`.
  2. Заполнить в `infra/.env` `SELECTELV2_USERNAME`, `SELECTELV2_PASSWORD`, `SELECTELV2_ACCOUNT_ID`, `SELECTELV2_PROJECT_ID`.
  3. Указать `TLS_MODE=letsencrypt` и `ACME_SERVER=letsencrypt-staging`, затем деплой через Ansible (`ansible/site.yml`).
  4. Проверить, что выдан staging-сертификат. Браузер на нём ругается, это нормально: в issuer стоит «(STAGING)».
  5. Указать `ACME_SERVER=letsencrypt` и снова деплой.
- **Продление**: systemd-таймер `anki-acme-renew.timer` раз в сутки в 04:00 МСК (01:00 UTC), без случайной задержки. Логи: `journalctl -u anki-acme-renew`. Ручной запуск на ноде: `sudo bash /srv/myapp/acme/renew.sh`. Nginx перечитывает сертификат только при его смене.
- **Откат**: `TLS_MODE=selfsigned` и деплой. Таймер выключается, данные Let's Encrypt остаются в `acme-data/`.
- **Wildcard и дополнительные имена**: `ACME_EXTRA_DOMAINS` (через пробел, например `*.ecb.tonzer.ru`). При изменении списка доменов выпускается новый сертификат.
- **Файлы на ноде** (`/srv/myapp`): `certs/` — активная пара; `certs/selfsigned/` — запасной самоподписанный; `acme-data/certificates/<host>-<server>.*` — сертификаты Let's Encrypt и ключ аккаунта ACME. `acme-data/` в git не попадает.

## Проверка каркаса (критерии готовности этапа 1)

Каждый Java-сервис при старте объявляет свою топологию AMQP и предоставляет тестовый эндпоинт
`POST /internal/test/ping` для проверки идемпотентности и DLQ (это инфраструктурная заглушка,
бизнес-логики в ней нет).

1. **Всё поднялось, health зелёный, Swagger открывается** — три ссылки выше.
2. **Идемпотентность** (событие дважды с одним `eventId` обработано один раз):
   ```bash
   # взять любой сервис, например card-builder (8083)
   ID=$(uuidgen)
   curl -s -X POST "http://localhost:8083/internal/test/ping?eventId=$ID"
   curl -s -X POST "http://localhost:8083/internal/test/ping?eventId=$ID"
   ```
   В логах: первое событие обработано, второе — `Duplicate event ... ignored`.
   В таблице `processed_event` одна строка на этот `eventId`.
3. **DLQ после 3 попыток** (событие падает в обработчике):
   ```bash
   curl -s -X POST "http://localhost:8083/internal/test/ping?fail=true"
   ```
   Обработчик кидает исключение, Spring AMQP повторяет 3 раза (backoff 1s/5s), затем
   сообщение уходит в `card-builder.test.ping.v1.dlq`.
4. **В RabbitMQ UI** (:15672) видны exchange `anki.events`, DLX `anki.events.dlx`,
   очереди потребителей и их `.dlq`.

> Эндпоинт `/internal/test/ping` — временная проверочная заглушка этапа 1. С этапа 6 порты сервисов
> не публикуются, а `/internal/**` через gateway отдаёт 404. Чтобы выполнить проверки выше, нужно
> запускать их изнутри сети compose, например `docker compose exec card-builder <команда>`
> (в образе должен быть нужный инструмент), либо временно добавить `ports` в локальный override-файл.
> Заглушку можно убрать после этапа 7.

## Базы данных
См. `postgres/README.md`.

## Billing (YooKassa sandbox)

В инфраструктурном Compose `billing-service` подключается к отдельной базе `billing_sandbox_db` и роли `BILLING_SANDBOX_DB_USER` в общем контейнере `postgres:17`. Для неё используется опубликованный общий порт PostgreSQL 5432; отдельного контейнера, изолированного порта и отдельного volume Billing нет. Переменные перечислены в `.env.example`; `YOOKASSA_RETURN_URL` формируется как `https://${PUBLIC_HOST}/billing`. При запуске с пустым `postgres-data` init-скрипт автоматически создаёт все базы и роли, включая Billing; затем сервисы применяют свои миграции. Ручное создание Billing-БД при чистом запуске не требуется. Подробности — в `postgres/README.md`.

Webhook: `POST /api/billing/webhooks/yookassa`. Требуется публичный HTTPS с доверенным сертификатом. События: `payment.succeeded`, `payment.canceled`, `payment.waiting_for_capture`.

Текущие начальные миграции рассчитаны на новую sandbox-БД и RabbitMQ vhost. Для существующих БД требуется отдельная миграция; удаление рабочих volumes не является путём обновления.

## Existing-realm SMTP update

Явный `python3 auth-keycloak/provision-smtp.py --apply` обновляет SMTP только в существующем realm через kcadm, используя выбранные Compose project/env-file и service `keycloak`. Укажите `--project-directory`, `--compose-file` и `--env-file` для расположения checkout; команды для checkout и `/srv/myapp` приведены в [auth-keycloak README](../auth-keycloak/README.md). Default Compose и Ansible не меняются.

HTTP endpoint теперь определяется из того же выбранного keycloak service/index:
один running instance и один published8080 loopback binding (127.0.0.1 или [::1]),
local Unix-socket Docker daemon. Fixed8180 fallback отсутствует; текущая
127.0.0.1:8180:8080 публикация поддерживается. Relative compose/env paths считаются
от project directory, inherited SMTP shell interpolation сохраняется.
DOCKER_HOST и DOCKER_CONTEXT одновременно nonempty запрещены до Compose/auth;
каждый отдельно должен выбирать local Unix socket. Exact version проверяет
selected container kc.sh --version, не privileged REST serverinfo.
JWT role gate удалён; intended update авторизует server manage-realm, GET success
не является доказательством manage authority. Source regression/integration matrix
добавлен. На docker-vm все38 focused regressions прошли;4 protected-filesystem
cases skipped,13 integration cases не запускались из-за отсутствия root/sudo.
Image digest и runtime outcomes неизвестны. API evidence:
[SMTP API verification](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/docs/smtp-api-verification.md).

Передаётся актуальный SMTP password из выбранной Compose-конфигурации даже при повторном запуске; GET маскирует пароль, его equality проверить нельзя. Команда сравнивает остальную структуру realm, но не проверяет доставку и не отправляет письмо. Сериализуйте внешнее администрирование: GET-merge-PUT не имеет CAS или atomicity. После ошибки во время записи обновление могло произойти; сначала сверьте realm. Runtime/deployed результат не проверялся.

## Task065 — notification (2026-11-19, source-only)

Добавлен internal `notification`, build context `./anki-gen-notification`,
remote `git@github.com:KriDan-Tech/anki-gen-notification.git` в app_repos.
Private clone выполняется на **Ansible controller** с become:false, затем rsync
на /srv/myapp. Target deploy SSH key сам по себе не даёт controller repo access.
Optional app_repos[].key_file — private key path на controller; ключи не commit'ить.

По уточнению владельца 2026-11-19 выбран чистый запуск стенда с нуля.
Notification DB создаётся общим `create_service_db` в
`postgres/init/01-databases.sh`, как базы остальных сервисов:
notification_sandbox_db + NOTIFICATION_DB_USER/PASSWORD из private .env.
Задайте отдельные credentials для notification. Init выполняется только на пустом
postgres-data; отдельного PostgreSQL-start/DB-provision шага Ansible и отдельного
notification DB script/mount больше нет. Ansible сохраняет обычный build/start
стека и proxy restart. Existing volumes автоматически не дополняются и не очищаются.
Исторический deployed deck V1 history/schema mismatch остаётся вопросом отдельного
reconciliation при переиспользовании старой БД; чистый запуск не является upgrade
её истории. Flyway repair/переписывание V1 не добавлены.

Notification получает shared семь SMTP_* vars и dedicated
NOTIFICATION_DIRECTORY_CLIENT_SECRET, не bootstrap/billing secret.
Все семь SMTP_* пусты → внутренний Mailpit mailpit:1025 no TLS/auth; partial external
config запрещён. Внешний SMTP требует starttls(required) либо implicit tls,
certificate/hostname checks и bounded timeouts.
Existing Keycloak realm нужен dedicated provisioner из auth-keycloak README;
его запуск не автоматизирован и здесь не выполнялся.
Notification health не зависит от Keycloak/SMTP: отсутствующий directory доступ
задерживает persisted jobs, после восьми attempts они DEAD.
Public send API/port/proxy route не добавляется.

Rabbit data теперь имеет named volume rabbitmq-data и stable hostname rabbitmq. На existing окружении
подключение нового volume скрывает прежний container-local data directory:
до отдельно разрешённого rollout оператор должен оценить/migrate существующие
queues/messages, а не считать такой переход сохранением старого broker state.
PostgreSQL17/RabbitMQ4 tags закрепляют major, не exact patches.

Документы сервиса: [polyrepo notification README](../notification/README.md);
standalone mirror: [notification](docs/project/services/notification.md).
No build/tests/validation/deploy/provision/send performed. Любое будущее отдельно
разрешённое исполнение — только docker-vm ответственным оператором.
