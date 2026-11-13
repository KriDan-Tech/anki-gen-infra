# Task043 — полный стенд header-processing-vNext

## Область передачи

Это подготовка к ручной приёмке владельцем, не заявление об успешном E2E.
Исходники публикуются в ветках ниже по запросу владельца от 2026-11-13.
Deployment не выполнялся; публикация не подтверждает E2E.
`第N課` — допустимые названия уроков; алгоритм заголовков не заменяется.

## Что собирать

Нужны ветки из списка ниже, а не обычный checkout `main` для всех сервисов.
Существующий Ansible fetch (`force: true`)/sync (`delete: true`) может
перезаписать рабочие деревья: сначала сохранить свою рабочую копию.

- KriDan-Tech/anki-gen-source-service: `feat/header-processing-vNext` для trial;
  `feat/section-aware-extraction` — отдельная baseline/header-first линия.
- KriDan-Tech/anki-gen-vocab-extractor: те же две раздельные ветки.
- KriDan-Tech/anki-web-frontend: `feat/section-aware-extraction`.
- KriDan-Tech/anki-gen-infra: `main` (этот документ).
- Остальные сервисы из таблицы: `main`, без изменений в этой передаче.

Не смешивать baseline source/extractor с vNext migration history.

| Сервис | Исходный каталог | Каталог относительно infra/docker-compose.yml |
|---|---|---|
| source-service | /home/srvadmin/projects/dev-anki-gen-header-vnext/source-service | anki-gen-source-service |
| vocab-extractor | /home/srvadmin/projects/dev-anki-gen-header-vnext/vocab-extractor | anki-gen-vocab-extractor |
| web-frontend | /home/srvadmin/projects/dev-anki-gen/web-frontend | anki-web-frontend |
| api-gateway | /home/srvadmin/projects/dev-anki-gen/api-gateway | anki-gen-api-gateway |
| card-builder | /home/srvadmin/projects/dev-anki-gen/card-builder | anki-gen-card-builder |
| deck-service | /home/srvadmin/projects/dev-anki-gen/deck-service | anki-gen-deck-service |
| billing-service | /home/srvadmin/projects/dev-anki-gen/billing-service | anki-gen-billing-service |
| keycloak | /home/srvadmin/projects/dev-anki-gen/auth-keycloak | anki-gen-auth-keycloak |

Infra берётся из `/home/srvadmin/projects/dev-anki-gen/infra`. При переносе
исходников исключать `.git`, `.env`, `node_modules`, `target`, `.venv`,
`__pycache__`; секреты стенда настраивать отдельно. Не копировать БД JA32.
Build/test/OCR/inference выполняются только на `docker-vm`, не на OpenClaw.

## Важное условие: истории миграций расходятся

Нельзя просто заменить source/extractor у существующей основной БД:

- vNext source: `0003_block_layout -> 0004_header_vnext`;
- основной source: `0003_block_layout -> 0004_header_first -> 0005_source_replacement`;
- vNext extractor: `V3__header_execution.sql`;
- основной extractor: `V3__extraction_recovery.sql`, затем `V4__header_first_work.sql`.

Рекомендуемая ручная приёмка — **отдельный пустой стенд** с отдельными БД,
очередями и томами. На отдельной чистой ВМ существующий Compose сам создаёт
sandbox-БД; Alembic/Flyway применяют неизменённые vNext-миграции. Этот вариант
не переносит старые задания и кошелёк. Существующие данные не удалять.

Если инфраструктура общая, перед стартом нужны новые пять БД
`source_vnext_trial_sandbox_db`, `extractor_vnext_trial_sandbox_db`,
`builder_vnext_trial_sandbox_db`, `deck_vnext_trial_sandbox_db`,
`billing_vnext_trial_sandbox_db` и отдельный vhost `anki-header-vnext-trial`.
Названия нужно переопределить **в environment соответствующих сервисов**:
`SOURCE_DB_NAME`, `EXTRACTOR_DB_NAME`, `BUILDER_DB_NAME`, `DECK_DB_NAME`,
`BILLING_DB_NAME`. Одних новых строк в `.env` недостаточно: базовый Compose
задаёт имена литералами. Пользователи/пароли должны иметь доступ именно к
новым БД; billing использует `BILLING_SANDBOX_DB_USER/PASSWORD` из `.env`.

В source/extractor/builder/deck одинаково переопределить `RABBITMQ_VHOST`
и `RABBITMQ_DEFAULT_VHOST`; сам vhost и права создать явно. Новое значение
`RABBITMQ_DEFAULT_VHOST` не создаёт vhost в уже работающем брокере.
Выделить отдельные source/export volumes и общий для trial сервисов
`BILLING_INTERNAL_SECRET`. Не подключать trial consumers к старым очередям.

Этот общий-инфраструктурный вариант требует подготовленного владельцем
override: базовый Compose имеет фиксированные `container_name` и порты;
одно `-p` не изолирует второй параллельный стек. На отдельной чистой ВМ этих
конфликтов нет. Не применять `stamp`, Flyway repair, подмену checksum,
переименование применённых миграций или `down -v` к существующему стенду.
Init PostgreSQL работает только на пустом data volume; для сохранённого
PostgreSQL новые БД создаются явно. In-place upgrade в эту передачу не входит.

## Конфигурация комплекса

- Все сервисы из таблицы нужны, включая card-builder и billing-service.
- Общий `BILLING_INTERNAL_SECRET` — не менее 32 символов.
- Рабочие DETECT и TRANSLATE настройки, соответствующие модели провайдера.
- `PUBLIC_HOST`, внешний issuer Keycloak, redirect URI браузера согласованы.
- Отдельные сохраняемые volumes исходников и экспортов.
- До запуска proxy положить сертификат для trial `PUBLIC_HOST` в
  `infra/certs/tls.crt` и закрытый ключ в `infra/certs/tls.key`; Compose
  монтирует каталог, но не выпускает сертификат. Использовать доверенный
  браузером сертификат (либо явно доверенный trial CA), ограничить доступ
  к ключу и не включать его в переносимые исходники/Git. Подготовка TLS
  отдельно: не запускать Ansible fetch/sync, перезаписывающие рабочие деревья.
- Proxy ожидает PROXY protocol от доверенного Traefik. Прямое HTTPS к нему
  без PROXY protocol не эквивалентно штатному входу; CIDR задать по `.env.example`.
- Пустая billing-БД не содержит баланса старого кошелька: перед платным стартом
  пополнить тестовый аккаунт штатным sandbox-процессом. Для создания оплаты
  обязательны `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` (sandbox-ключ
  с префиксом `test_`) и `YOOKASSA_EXPECTED_ACCOUNT_ID` соответствующего
  тестового магазина. Нужна доступность YooKassa из billing-service и
  рабочего checkout/подтверждения платежа; пустые defaults `.env.example`
  не подходят: создание заказа вернёт 503. Дождаться зачисления в кошелёк
  штатным UI/API до платного старта. Не копировать ledger.

## Ручная приёмка владельцем

1. Новый PDF загрузить через изменённый браузер. Новый запрос должен содержать
   `processingVersion: header-processing-vNext`; старый сохранённый источник
   без версии остаётся legacy. Дождаться `PARSED`.
2. Предпросмотр и платный старт должны использовать ту же версию и страницы.
   Quote/start оплачивают выбранные физические страницы; не повторять старт
   ради ожидания результата. Сохранённые платные команды повторяются неизменно.
3. Дождаться `AWAITING_REVIEW`: заголовки определены, отдельный OCR слов
   завершён, слова имеют теги `lesson::N` и дополнительные теги источника.
4. Принять нужные предложенные слова (или «принять все»), затем явно подтвердить
   сборку карточек. `autoConfirm: false` у новых vNext-запусков намеренно
   оставляет этот шаг владельцу. Непринятые PROPOSED слова в сборку не входят.
5. Убедиться, что card-builder получил `terms.confirmed.v1`, сформировал
   `cards.built.v1`, а deck-service показывает готовые карточки и их теги.
6. Проверить/одобрить карточки. Экспортировать `.apkg`; экспорт берёт только
   `APPROVED` карточки с учётом выбранного фильтра тегов, не `NEEDS_REVIEW`.

Предыдущие 32 страницы/120 слов JA32 подтверждали только достижение review
в изолированной среде. Там было 0 карточек/0 экспортов и отсутствовал builder;
это не является проверкой полного комплекса. Здесь повторные платные старты,
провайдерные прогоны, сборки и выкладка не выполняются.

## Источники статической сверки

Версии зависимостей не обновляются. Backend API evidence:
`dev-anki-gen-header-vnext/source-service/docs/header-vnext-api-evidence.md`,
`dev-anki-gen-header-vnext/vocab-extractor/docs/header-vnext-api-evidence.md`.
Контракты: source `app/routes.py`; extractor PaidPreviewService/PaidStartService,
ExtractionRunner/ExtractionService; builder TermsConfirmedListener;
deck ExportService/ExportController; gateway GatewayRoutes. Миграции и
переменные окружения проверяются по указанным деревьям и `infra/docker-compose.yml`.
