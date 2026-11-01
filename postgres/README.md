# postgres

Все сервисы инфраструктурного Compose используют общий контейнер `postgres` на образе
`postgres:17`; каждый сервис подключается к собственной базе и собственной роли-владельцу.
Billing использует собственную sandbox-базу и роль в этом же сервере.

## Базы и роли

| База | Владелец (роль) | Переменные env | Сервис |
|---|---|---|---|
| `keycloak_db` | `KEYCLOAK_DB_USER` | `KEYCLOAK_DB_USER` / `KEYCLOAK_DB_PASSWORD` | auth-keycloak (этап 6) |
| `source_sandbox_db` | `SOURCE_DB_USER` | `SOURCE_DB_USER` / `SOURCE_DB_PASSWORD` | source-service (этап 3) |
| `extractor_sandbox_db` | `EXTRACTOR_DB_USER` | `EXTRACTOR_DB_USER` / `EXTRACTOR_DB_PASSWORD` | vocab-extractor |
| `builder_sandbox_db` | `BUILDER_DB_USER` | `BUILDER_DB_USER` / `BUILDER_DB_PASSWORD` | card-builder |
| `deck_sandbox_db` | `DECK_DB_USER` | `DECK_DB_USER` / `DECK_DB_PASSWORD` | deck-service |
| `billing_sandbox_db` | `BILLING_SANDBOX_DB_USER` | `BILLING_SANDBOX_DB_USER` / `BILLING_SANDBOX_DB_PASSWORD` | billing-service (YooKassa sandbox) |

Базы `source_sandbox_db` и `keycloak_db` создаются заранее, хотя сами сервисы появляются на более поздних этапах —
чтобы init-скрипт не пришлось менять. `audio_db` в MVP нет.

## Инициализация

При запуске с пустым `postgres-data` официальный entrypoint образа PostgreSQL обрабатывает
`/docker-entrypoint-initdb.d`; `init/01-databases.sh` создаёт роли и отдельные базы всех
перечисленных сервисов, включая Billing. Схемы таблиц создают сервисы при запуске: Flyway
(Java-сервисы) и Alembic (source-service).

Init-скрипты выполняются только при первой инициализации пустого каталога данных. Уже
инициализированный `postgres-data` повторно их не выполняет; этот сценарий требует отдельной
подготовки базы и не меняет рабочие данные автоматически. Скрипт создаёт только базы и роли,
таблиц не трогает.

## Billing sandbox

Billing подключается к `billing_sandbox_db` в общем `postgres:17` через роль
`BILLING_SANDBOX_DB_USER`; пароль задаёт `BILLING_SANDBOX_DB_PASSWORD`. Инфраструктурный
Compose использует общий опубликованный порт PostgreSQL 5432; отдельного контейнера и volume
для Billing нет.

Для новой пустой Billing-базы данных перенос не нужен. Если требуется сохранить данные из
ранее использовавшейся отдельной базы Billing, это самостоятельный логический перенос:
остановите запись, сделайте backup, восстановите в совместимую целевую базу и проверьте
результат до переключения сервиса. Автоматического копирования данных или удаления прежнего
volume нет. При обновлении Compose `remove_orphans` может удалить старый контейнер, но
именованный volume прежней базы сохраняется.

При конфликте существующей роли, credentials или владельца остановитесь для отдельного
разбора; init-скрипт не выполняет автоматический ремонт и не меняет существующие объекты.
