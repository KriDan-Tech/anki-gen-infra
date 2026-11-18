# auth-keycloak

## Владение
Keycloak realm/client provisioning и identity. Gateway валидирует токены; приложение использует subject как пользовательскую идентичность. Подробности конфигурации — в `auth-keycloak/README.md`.

## Наблюдаемая реализация (2026-11-18)
Осмотрены также `auth-keycloak/provision-smtp.py`, `test_provision_smtp.py` и shared SMTP env mapping (2026-11-18). Offline prepare валидирует non-secret процессные значения; `--check` использует resolved Compose settings и локальный Admin REST только для чтения видимых SMTP значений. `--apply` fail-closed до Compose/network: подтверждено, что stock smtpServer-only PUT сбрасывает OAuth2 device (600/5), CIBA и PAR настройки; безопасный изолированный write design ещё не установлен. `--check` аутентифицируется (возможны session/audit side effects), затем только читает realm GET; SMTP/realm не меняет и письма не отправляет. См. `auth-keycloak/README.md` и исследовательские Task065 API notes.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `auth-keycloak/Dockerfile`, `realm-export.json`, `README.md`, `create-review-user.py`, `provision-billing-admin.py` (2026-11-16). Локальная ветка `main` @32ade4c. `auth-keycloak/Dockerfile` определяет базовый Keycloak image/tag; compose README указывает 26.8.1. Realm import при первом создании, provisioning semantics и named paths описывать по этим файлам. Секреты не документировать и не копировать.

## Утверждённая цель
Поддерживать пользовательскую аутентификацию для UI и выдавать identity, которую gateway проверяет; сервисы отделяют пользователя по ID. Google/login policies из старой архитектуры считать действующими только там, где они есть в текущей realm source.

## Разрывы и неизвестное
Проверка конфигурации не доказывает созданный realm, состояние провайдера/клиентов в работающем Keycloak или deployment. Не публиковать credentials, не обещать внешнее identity поведение только по Dockerfile.

## Практическая навигация (осмотр 2026-11-16)
[Dockerfile](../../auth-keycloak/Dockerfile) задаёт pinned image/startup import; [realm-export.json](../../auth-keycloak/realm-export.json) — декларативную конфигурацию realm; [README](../../auth-keycloak/README.md) и scripts [create-review-user.py](../../auth-keycloak/create-review-user.py), [provision-billing-admin.py](../../auth-keycloak/provision-billing-admin.py) — provisioning entrypoints. Секретные значения не копируются в docs; checked-in realm не доказывает его применённое состояние.
