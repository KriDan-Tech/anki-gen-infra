# postgres

Все сервисы инфраструктурного Compose используют общий контейнер `postgres` на образе
`postgres:17`; каждый сервис подключается к собственной базе и собственной роли-владельцу.
Billing использует собственную базу и роль в этом же сервере.

## Базы и роли

| База | Владелец (роль) | Переменные env | Сервис |
|---|---|---|---|
| `keycloak_db` | `KEYCLOAK_DB_USER` | `KEYCLOAK_DB_USER` / `KEYCLOAK_DB_PASSWORD` | auth-keycloak (этап 6) |
| `source_sandbox_db` | `SOURCE_DB_USER` | `SOURCE_DB_USER` / `SOURCE_DB_PASSWORD` | source-service (этап 3) |
| `extractor_sandbox_db` | `EXTRACTOR_DB_USER` | `EXTRACTOR_DB_USER` / `EXTRACTOR_DB_PASSWORD` | vocab-extractor |
| `builder_sandbox_db` | `BUILDER_DB_USER` | `BUILDER_DB_USER` / `BUILDER_DB_PASSWORD` | card-builder |
| `deck_sandbox_db` | `DECK_DB_USER` | `DECK_DB_USER` / `DECK_DB_PASSWORD` | deck-service |
| `billing_sandbox_db` (по умолчанию) | `BILLING_SANDBOX_DB_USER` | `BILLING_DB_NAME` / `BILLING_SANDBOX_DB_USER` / `BILLING_SANDBOX_DB_PASSWORD` | billing-service |
| `notification_sandbox_db` | `NOTIFICATION_DB_USER` | `NOTIFICATION_DB_USER` / `NOTIFICATION_DB_PASSWORD` | notification |

Базы `source_sandbox_db` и `keycloak_db` создаются заранее, хотя сами сервисы появляются на более поздних этапах —
чтобы init-скрипт не пришлось менять. `audio_db` в MVP нет.

## Инициализация

При запуске с пустым `postgres-data` официальный entrypoint образа PostgreSQL обрабатывает
`/docker-entrypoint-initdb.d`; `init/01-databases.sh` создаёт роли и отдельные базы всех
перечисленных сервисов, включая Billing и notification. Схемы таблиц создают сервисы при запуске: Flyway
(Java-сервисы) и Alembic (source-service).

Init-скрипты выполняются только при первой инициализации пустого каталога данных. Уже
инициализированный `postgres-data` повторно их не выполняет; этот сценарий требует отдельной
подготовки базы и не меняет рабочие данные автоматически. Скрипт создаёт только базы и роли,
таблиц не трогает.

## Billing

Compose передаёт одинаковое имя `BILLING_DB_NAME` в `billing-service` и `postgres` для первой
инициализации. Если переменная не задана или пуста, Compose и init-скрипт при отдельном вызове
используют `billing_sandbox_db`. Billing подключается к этой базе в общем `postgres:17` через роль
`BILLING_SANDBOX_DB_USER`; пароль задаёт `BILLING_SANDBOX_DB_PASSWORD`. Инфраструктурный
Compose использует общий опубликованный порт PostgreSQL 5432; отдельного контейнера и volume
для Billing нет.

На существующем `postgres-data` изменение имени только меняет целевую базу подключения:
автоматического создания, переименования или сброса нет. Подготовьте целевую базу отдельно
до переключения, не удаляя volume. При имени, отличном от `billing_sandbox_db`, переопределите
`backup_databases` в Ansible inventory: включите новое имя Billing-БД в полный список, сохранив
остальные базы из `ansible/roles/postgres_backup_cron/defaults/main.yml`.

Для новой пустой Billing-базы данных перенос не нужен. Если требуется сохранить данные из
ранее использовавшейся отдельной базы Billing, это самостоятельный логический перенос:
остановите запись, сделайте backup, восстановите в совместимую целевую базу и проверьте
результат до переключения сервиса. Автоматического копирования данных или удаления прежнего
volume нет. При обновлении Compose `remove_orphans` может удалить старый контейнер, но
именованный volume прежней базы сохраняется.

При конфликте существующей роли, credentials или владельца остановитесь для отдельного
разбора; init-скрипт не выполняет автоматический ремонт и не меняет существующие объекты.

## Task065 — notification database (2026-11-19)

Уточнение владельца 2026-11-19 заменяет прежнюю targeted-подготовку:
стенд будет пересоздан с нуля, notification использует тот же
`create_service_db "notification_sandbox_db" "${NOTIFICATION_DB_USER}" "${NOTIFICATION_DB_PASSWORD}"`
в `init/01-databases.sh`, что остальные service DBs.
Задайте отдельную роль/пароль в private .env. Новая роль создаётся обычным
CREATE ROLE LOGIN (без superuser grants), база — с этой ролью-владельцем.
Отдельный notification provisioning script/mount и предварительные DB tasks
Ansible удалены. Дополнительных проверок reused roles/owner или отдельного
PUBLIC revoke теперь нет: это обычный существующий helper, не upgrade/repair.
Параметры по-прежнему передаются через quoted psql variables/format %I/%L.

Init запускается только с пустым postgres-data; existing cluster автоматически
не дополняется. Код не удаляет volumes и не повторяет initializer на старой БД.
Known deployed deck V1 history/schema mismatch сохранён как исторический caveat
для reuse старой deck DB, не как требование чинить историю при чистом запуске.
Flyway repair/переписывание V1 не добавлены.

Exact source references: PostgreSQL17
https://www.postgresql.org/docs/17/sql-createrole.html ,
https://www.postgresql.org/docs/17/app-psql.html .
SQL execution/permissions/concurrency не проверялись; только source authored.
Будущее отдельно разрешённое исполнение — docker-vm.
