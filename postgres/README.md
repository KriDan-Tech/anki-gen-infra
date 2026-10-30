# postgres

Основные сервисы используют контейнер `postgres`; billing — отдельный `billing-sandbox-db`.
У каждого сервиса — своя база и свой пользователь
(ARCHITECTURE §7, план §1.4). В чужие базы сервисы не ходят.

## Базы и роли

| База | Владелец (роль) | Переменные env | Сервис |
|---|---|---|---|
| `keycloak_db`  | `KEYCLOAK_DB_USER`  | `KEYCLOAK_DB_USER` / `KEYCLOAK_DB_PASSWORD`   | auth-keycloak (этап 6) |
| `source_sandbox_db`    | `SOURCE_DB_USER`    | `SOURCE_DB_USER` / `SOURCE_DB_PASSWORD`       | source-service (этап 3) |
| `extractor_sandbox_db` | `EXTRACTOR_DB_USER` | `EXTRACTOR_DB_USER` / `EXTRACTOR_DB_PASSWORD` | vocab-extractor |
| `builder_sandbox_db`   | `BUILDER_DB_USER`   | `BUILDER_DB_USER` / `BUILDER_DB_PASSWORD`     | card-builder |
| `deck_sandbox_db`      | `DECK_DB_USER`      | `DECK_DB_USER` / `DECK_DB_PASSWORD`           | deck-service |

Базы `source_sandbox_db` и `keycloak_db` создаются заранее, хотя сами сервисы появляются на более поздних этапах —
чтобы init-скрипт не пришлось менять. `audio_db` в MVP нет.

## init/01-databases.sh

Создаёт роли и базы основных сервисов из таблицы выше в контейнере `postgres`.
Billing-БД этот скрипт не создаёт. Пароли передаются через переменные окружения Compose.

**Важно:** скрипт выполняется только при **первой** инициализации пустого каталога данных
(стандартный механизм образа postgres — `/docker-entrypoint-initdb.d`). Если контейнер уже
инициализировался, повторно скрипт не запустится.

Повторный запуск Compose не добавляет базы в уже инициализированный volume. Для существующих
инсталляций требуется отдельная подготовка баз и миграция; рабочие volumes удалять не нужно.

## Billing sandbox

| Параметр | Значение |
|---|---|
| Контейнер | `billing-sandbox-db` (`postgres:17`) |
| База | `billing_sandbox_db` |
| Роль | `billing_sandbox` |
| Пароль | `BILLING_SANDBOX_DB_PASSWORD` |
| Volume | `billing-sandbox-data` |
| Доступ | Только внутри сети Compose, порт на хост не опубликован |

Базу и роль создаёт стандартный entrypoint образа PostgreSQL через `POSTGRES_DB` и
`POSTGRES_USER` при первой инициализации пустого volume. `billing-service` получает
подключение через `BILLING_DB_HOST`, `BILLING_DB_NAME`, `BILLING_DB_USER`, `BILLING_DB_PASSWORD`;
Compose передаёт пароль из `BILLING_SANDBOX_DB_PASSWORD`.

Схему billing создаёт Flyway при запуске сервиса. Начальные миграции рассчитаны на новую
sandbox-БД; для уже установленной схемы требуется отдельная миграция. Изменение пароля
в окружении само по себе не меняет пароль роли в существующем volume.

Миграции схемы внутри каждой базы делает сам сервис: Flyway (Java-сервисы), Alembic (source-service).
init-скрипт только создаёт базы и роли, таблиц не трогает.
