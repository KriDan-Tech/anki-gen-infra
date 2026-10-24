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
