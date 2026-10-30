# infra

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
| acme | `goacme/lego:v5.5.2` | — | разовый запуск: выпуск/продление LE |

**Наружу публикуются только gateway (8080), Keycloak (8180) и Mailpit (8025).** Порты сервисов
(8081–8084) с этапа 6 в compose не публикуются: всё идёт через gateway. Postgres и RabbitMQ пока
доступны с хоста (см. открытые вопросы в отчёте этапа 6).
**Redis не используется.** `audio-service` — вне MVP.

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

## YooKassa sandbox (owner-run only)

Sandbox only: TEST credits are not production entitlements, and there is no live-money mode. Billing has a dedicated `billing-sandbox-db`/`billing-sandbox-data` volume with no published port. Never use a live shop. The billing service and application repositories are checked out by the existing Ansible `app_repos` list; rollout remains the owner-run `ansible/site.yml` workflow (see the repository's normal inventory/SSH setup). Do not run a separate deployment path.

Before rollout, set `PUBLIC_HOST` to the existing public host (the return URL is generated as `https://${PUBLIC_HOST}/billing`) and prepare the test shop credentials/catalogue. Exact ready-to-copy keys and safe placeholder values:

```dotenv
BILLING_SANDBOX_DB_PASSWORD=REPLACE_WITH_UNIQUE_SANDBOX_DB_PASSWORD
YOOKASSA_SHOP_ID=REPLACE_WITH_TEST_SHOP_ID
YOOKASSA_SECRET_KEY=test_REPLACE_WITH_TEST_SHOP_SECRET
# The verified recipient.account_id expected in authoritative payment GET responses;
# do not assume this equals the shop ID.
YOOKASSA_EXPECTED_ACCOUNT_ID=REPLACE_WITH_EXPECTED_RECIPIENT_ACCOUNT_ID
# Replace [] with owner-selected, valid JSON package definitions; keep the single quotes.
BILLING_PACKAGES_JSON='[{"id":"owner-selected-id","title":"Owner-selected title","amountKopecks":10000,"credits":100}]'
# Replace with a randomly generated secret of at least 32 characters.
BILLING_INTERNAL_SECRET=REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS
# Owner-selected nonnegative integer credit rates; zero is permitted.
BILLING_PAGE_X_CREDITS=0
BILLING_PAGE_Y_CREDITS=0
BILLING_TARIFF_VERSION=1
```

The package example is syntax-only: choose the actual ID, title, amount in kopecks, and credits before enabling checkout. Do not leave example credentials or a placeholder catalogue in use. Keep `.env` private (`chmod 600`); never commit it. The existing compose configuration generates `YOOKASSA_RETURN_URL` from `PUBLIC_HOST`.

Before the owner runs the existing Ansible rollout, register the exact HTTPS `POST https://PUBLIC_HOST/api/billing/webhooks/yookassa` notification in the test-shop cabinet for `payment.succeeded`, `payment.canceled`, and `payment.waiting_for_capture`. The endpoint must be publicly reachable over HTTPS with a trusted certificate. Use only test-shop credentials (the code also enforces the local `test_` prefix gate); provider credential format has an outstanding verification caveat documented in `anki-gen-billing-service/docs/api-verification.md`.

Billing uses edited initial V1 migrations. Use fresh, separate sandbox databases and the dedicated RabbitMQ vhost; never apply edited initial migrations to existing databases/vhosts. Do not delete existing volumes as a shortcut. See `anki-gen-billing-service/README.md` for service-level details.
