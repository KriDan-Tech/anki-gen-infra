# auth-keycloak

## Владение
Keycloak realm/client provisioning и identity. Gateway валидирует токены; приложение использует subject как пользовательскую идентичность. Подробности конфигурации — в `auth-keycloak/README.md`.

## Наблюдаемая реализация (2026-11-18)
Осмотрены `auth-keycloak/provision-smtp.py`, `auth-keycloak/Dockerfile`, `auth-keycloak/realm-export.json`, `infra/docker-compose.yml` и `infra/docker-compose.smtp-import.yml` (2026-11-18). `--prepare-import` разрешает SMTP из Compose в памяти и атомарно формирует защищённый `anki-gen-realm.json`; при семи отсутствующих/пустых значениях сохраняется Mailpit template, внешняя конфигурация проходит общую валидацию. Экспорт не отправляется в stdout и не вызывает Admin/SMTP. Dockerfile по-прежнему содержит baked-in realm; необязательный Compose override bind-mount'ит подготовленный каталог поверх `/opt/keycloak/data/import` только при явном включении. Default Compose/Ansible не меняются. Первый импорт не обновляет существующий realm. Обычный offline mode остаётся без Compose/network. `--check` использует resolved Compose settings и локальный Admin REST для чтения видимых SMTP значений; аутентификация может создать session/audit state, email не отправляется. Явный `--apply` использует Keycloak 26.8.1 kcadm GET-merge-PUT для существующего realm; bare smtpServer-only PUT не применяется. Проверяются версия сервера, admin roles и полнота обычного realm GET; after-write сверяются видимые SMTP значения и весь realm projection вне `smtpServer`. Реальный password передаётся каждый раз, GET его маскирует. Delivery не тестируется. External admin changes должны быть сериализованы; CAS/atomicity/retry/rollback отсутствуют. Runtime/deployed state не проверялся. См. `auth-keycloak/README.md`.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `auth-keycloak/Dockerfile`, `realm-export.json`, `README.md`, `create-review-user.py`, `provision-billing-admin.py` (2026-11-16). Локальная ветка `main` @32ade4c. `auth-keycloak/Dockerfile` определяет базовый Keycloak image/tag; compose README указывает 26.8.1. Realm import при первом создании, provisioning semantics и named paths описывать по этим файлам. Секреты не документировать и не копировать.

## Утверждённая цель
Поддерживать пользовательскую аутентификацию для UI и выдавать identity, которую gateway проверяет; сервисы отделяют пользователя по ID. Google/login policies из старой архитектуры считать действующими только там, где они есть в текущей realm source.

## Разрывы и неизвестное
Проверка конфигурации не доказывает созданный realm, состояние провайдера/клиентов в работающем Keycloak или deployment. Не публиковать credentials, не обещать внешнее identity поведение только по Dockerfile.

## Практическая навигация (осмотр 2026-11-16)
[Dockerfile](../../auth-keycloak/Dockerfile) задаёт pinned image/startup import; [realm-export.json](../../auth-keycloak/realm-export.json) — декларативную конфигурацию realm; [README](../../auth-keycloak/README.md) и scripts [create-review-user.py](../../auth-keycloak/create-review-user.py), [provision-billing-admin.py](../../auth-keycloak/provision-billing-admin.py) — provisioning entrypoints. Секретные значения не копируются в docs; checked-in realm не доказывает его применённое состояние.

## Task065 — notification-directory, source-only 2026-11-19

Осмотрены/написаны `auth-keycloak/provision-notification-directory.py` и staged
client в `realm-export.json`; исходный `Dockerfile` pin-ит Keycloak26.8.1.
Новый standalone idempotent existing-realm provisioner использует client credentials
service account, fullScopeAllowed=false, view-users mapping + scope и role mapper.
Проверяет exact fixed composite closure query-users/query-groups, исключает
manage-users/realm-admin/прочие effective management roles. До проверки новых
account privileges client staged disabled; после writes — read-back verification.
Billing и SMTP provisioners не менялись.

Цель: runtime notification exact-ID user lookup без email из events/search и без
bootstrap/billing credentials. Enabled + emailVerified + single valid mailbox,
иначе suppression. Runtime получает только dedicated secret.
Ничего не provisioned/deployed, письма не отправлялись. Realm import не обновляет
existing realm; helper запускает отдельно авторизованный оператор только docker-vm.
Источники/API gaps: [notification API notes](../../notification/docs/api-verification.md).

## SMTP admin token lifetime — source fix 2026-11-19

Источники: `auth-keycloak/provision-smtp.py`, `test_provision_smtp.py`,
[SMTP API evidence](../../auth-keycloak/docs/smtp-api-verification.md).
Удалён локальный порог expires_in>180, который отвергал успешный ответ с валидным
коротким token (например 60s) как authentication failed; это не доказывало ошибку
credentials. Token/TTL shape и положительный integer lifespan по-прежнему проверяются.

expiresAt отражает conservative acquisition-start + реальный TTL; elapsed time
и monotonic deadline ограничивают --check/--apply. Перед kcadm timeout динамически
ограничивается remaining lifetime с запасом на его pinned 5s refresh threshold,
1s clock margin и 10s readback. Недостаточный budget отклоняется до запуска update
с отдельной sanitized причиной; после запуска ошибки остаются may-have-occurred.
Refresh/lifespan/privileges не меняются; full realm GET-merge-PUT preservation
и drift verification сохранены. Source regressions добавлены без исполнения;
live auth/provision/send/deploy не выполнялись, future execution только docker-vm.

## SMTP target authority — source fix 2026-11-19

В master-issued admin token локальная проверка теперь распознаёт именно
resource_access["anki-gen-realm"].roles/manage-realm, а не realm-local
realm-management или произвольные одноимённые роли. Master admin composite
по-прежнему принимается; view-only, чужой realm и malformed claims отклоняются.
Для операции нужен manage-realm, не весь набор realm-admin permissions.

Это подтверждённый source false-negative прежнего gate, но production token shape
не установлен. Missing/opaque/lightweight claims дают отдельный local-preflight
отказ без update, не утверждение об отсутствии реальных server privileges.
Full realm GET допускает view-realm и сам по себе не доказывает manage-realm.
Server enforcement, full-realm preservation и short-token fencing сохранены;
эквивалентный read-only manage preflight для admin-cli не установлен.
Pinned Keycloak26.8.1 sources, regression sources и unknowns:
[SMTP API evidence](../../auth-keycloak/docs/smtp-api-verification.md).
Никаких auth/runtime/tests/provision/deploy/send execution не выполнялось.
