# postgres

Один контейнер PostgreSQL на весь проект. У каждого сервиса — своя база и свой пользователь
(ARCHITECTURE §7, план §1.4). В чужие базы сервисы не ходят.

## Базы и роли

| База | Владелец (роль) | Переменные env | Сервис |
|---|---|---|---|
| `keycloak_db`  | `KEYCLOAK_DB_USER`  | `KEYCLOAK_DB_USER` / `KEYCLOAK_DB_PASSWORD`   | auth-keycloak (этап 6) |
| `source_db`    | `SOURCE_DB_USER`    | `SOURCE_DB_USER` / `SOURCE_DB_PASSWORD`       | source-service (этап 3) |
| `extractor_db` | `EXTRACTOR_DB_USER` | `EXTRACTOR_DB_USER` / `EXTRACTOR_DB_PASSWORD` | vocab-extractor |
| `builder_db`   | `BUILDER_DB_USER`   | `BUILDER_DB_USER` / `BUILDER_DB_PASSWORD`     | card-builder |
| `deck_db`      | `DECK_DB_USER`      | `DECK_DB_USER` / `DECK_DB_PASSWORD`           | deck-service |

Базы `source_db` и `keycloak_db` создаются заранее, хотя сами сервисы появляются на более поздних этапах —
чтобы init-скрипт не пришлось менять. `audio_db` в MVP нет.

## init/01-databases.sh

Создаёт роли и базы из таблицы выше. Пароли берутся из env (см. `infra/.env`, шаблон `infra/.env.example`).

**Важно:** скрипт выполняется только при **первой** инициализации пустого каталога данных
(стандартный механизм образа postgres — `/docker-entrypoint-initdb.d`). Если контейнер уже
инициализировался, повторно скрипт не запустится.

Чтобы пересоздать базы с нуля:

```bash
docker compose down
docker volume rm dev-anki-gen_postgres-data   # имя = <project>_postgres-data
docker compose up -d postgres
```

Миграции схемы внутри каждой базы делает сам сервис: Flyway (Java-сервисы), Alembic (source-service).
init-скрипт только создаёт базы и роли, таблиц не трогает.
