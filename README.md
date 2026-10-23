# infra

Инфраструктура и запуск всего проекта dev-anki-gen. Своего кода здесь нет — только
`docker-compose.yml`, init-скрипты Postgres и переменные окружения (полирепо, см. STRUCTURE.md).
Сервисы собираются из соседних репозиториев через `build.context: ../<сервис>`.

## Что поднимается (этап 1 — каркас)

| Контейнер | Образ | Порты (dev) | Назначение |
|---|---|---|---|
| postgres | `postgres:17` | 5432 | Один сервер, отдельная база на сервис |
| rabbitmq | `rabbitmq:4-management` | 5672, 15672 | Брокер событий + management UI |
| mailpit | `axllent/mailpit` | 8025, 1025 | Заглушка SMTP (для Keycloak, этап 6) |
| vocab-extractor | build `../vocab-extractor` | 8082 | Каркас сервиса (Java) |
| card-builder | build `../card-builder` | 8083 | Каркас сервиса (Java) |
| deck-service | build `../deck-service` | 8084 | Каркас сервиса (Java) |

`api-gateway`, `auth-keycloak`, `source-service` добавляются на своих этапах (6, 6, 3).
**Redis не используется.** `audio-service` — вне MVP.

## Запуск

```bash
cp .env.example .env         # заполнить пароли и (для этапов 2+) ИИ-ключи
chmod 600 .env
docker compose up -d --build
```

- Swagger UI сервисов: http://localhost:8082/swagger-ui.html, :8083, :8084
- Health: http://localhost:8082/actuator/health (и :8083, :8084)
- RabbitMQ UI: http://localhost:15672 (логин/пароль из `RABBITMQ_DEFAULT_*`)
- Mailpit UI: http://localhost:8025

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

> Эндпоинт `/internal/test/ping` — временная проверочная заглушка этапа 1. На этапе 6
> префикс `/internal/**` закрывается снаружи gateway; к тому времени заглушку можно убрать.

## Базы данных
См. `postgres/README.md`.
