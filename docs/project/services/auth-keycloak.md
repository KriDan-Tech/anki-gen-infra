# auth-keycloak

## Владение
Keycloak realm/client provisioning и identity. Gateway валидирует токены; приложение использует subject как пользовательскую идентичность. Подробности конфигурации — в `auth-keycloak/README.md`.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `auth-keycloak/Dockerfile`, `realm-export.json`, `README.md`, `create-review-user.py`, `provision-billing-admin.py` (2026-11-16). Локальная ветка `main` @32ade4c. `auth-keycloak/Dockerfile` определяет базовый Keycloak image/tag; compose README указывает 26.8.1. Realm import при первом создании, provisioning semantics и named paths описывать по этим файлам. Секреты не документировать и не копировать.

## Утверждённая цель
Поддерживать пользовательскую аутентификацию для UI и выдавать identity, которую gateway проверяет; сервисы отделяют пользователя по ID. Google/login policies из старой архитектуры считать действующими только там, где они есть в текущей realm source.

## Разрывы и неизвестное
Проверка конфигурации не доказывает созданный realm, состояние провайдера/клиентов в работающем Keycloak или deployment. Не публиковать credentials, не обещать внешнее identity поведение только по Dockerfile.

## Практическая навигация (осмотр 2026-11-16)
[Dockerfile](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/Dockerfile) задаёт pinned image/startup import; [realm-export.json](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/realm-export.json) — декларативную конфигурацию realm; [README](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/README.md) и scripts [create-review-user.py](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/create-review-user.py), [provision-billing-admin.py](https://github.com/KriDan-Tech/anki-gen-auth-keycloak/blob/main/provision-billing-admin.py) — provisioning entrypoints. Секретные значения не копируются в docs; checked-in realm не доказывает его применённое состояние.
