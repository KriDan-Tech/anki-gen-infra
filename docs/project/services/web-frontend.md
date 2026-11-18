# web-frontend

## Task064 — default нового PDF (2026-11-18)

**Текущая цель владельца:** временно без lesson/header detection. Для новых
загрузок `api/models/source.ts` задаёт default `page-only.v1`;
`features/deck/add/pdf-upload-form.ts` сохраняет `staged=true` и
preview/start wire command `staged-pdf.v1`. Новый PDF не имеет custom tag input:
интерфейс объясняет automatic `book::<slug>` и `page::N` tags. Page-only
создаёт команду с autoConfirm=true для фактического создания карточек.
Text/manual paths и сохранённые команды с прежними settings не переписываются.

**Статически реализовано:** staged page-only eligibility не требует header
digest/snapshot. Активированный page-only source не получает новый quote:
пользователь продолжает сохранённую команду либо загружает PDF заново.
PARSED/FAILED/PURGED/CANCELLED — terminal observations. Historical header sources
остаются на exact historical route; UI явно предлагает повторную загрузку для
нового book/page пути, не конвертирует source/quote/job. Unknown-result replay
передаёт сохранённый request без изменения autoConfirm или версии.
Review Task064 (2026-11-18): после recreated-component restore с PARSED source и
потерянным accepted-start response matching pending PDF command текущего owner/source/deck
без extractionId получает видимую кнопку exact replay; rejected/чужая команда не
даёт recovery. Saved title/pages/request сохраняются, fresh quote/start остаётся
запрещён. Для новых PDF подготовительный текст не обещает whole-book heading analysis;
старый текст условен только для historical header profile. Regression source
проверяет destroyed/recreated component и реальную кнопку replay; не запускался.

**Неизвестное:** `pdf-page-only.spec.ts` написан, не запускался; tests/build/browser/
provider/deploy не выполнялись. Manifest: Angular22.2.3, TypeScript6.0.3;
Angular CLI22.2.4 — отдельный pin. Это source-only реализация, не runtime proof.
Будущие авторизованные исполнения только docker-vm.


## Владение
Пользовательский интерфейс для загрузки, выбора страниц, цены, оплаты, статуса обработки и управления deck. API wrappers и route tree — в исходниках; focused UI documentation stays in frontend repository.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `web-frontend/src/app/features/deck/add/pdf-upload-form.ts`, `features/extraction/extraction.page.ts`, API/model source, jobs polling source и package manifests (2026-11-16). Локальная ветка `feat/source-durable-progress-2026-11-16` @3e37943 с незакоммиченными Task054 изменениями. `web-frontend/package.json` README указывает Angular CLI 22.2.4; зависимости проверять по manifest этой ветки, не подразумевать production release.

## Утверждённая цель
Провести пользователя через загрузку → выбор страниц → quote → оплату → обработку → deck. Пользовательский start оплачивается один раз; внутренние retries не требуют повторной оплаты. Результат показывать после завершения, включая успешно полученные partial results согласно target; Draft без предварительного списка approval. Zero-word success само по себе не обещает refund.

## Разрывы и неизвестное
UI controls/polling отражают клиентскую реализацию, не гарантию backend billing or durable completion. Наблюдаемая autoConfirm/review и статусы могут не совпадать с новым решением; не выдавать frontend за доказательство сервисных гарантий. Внешние платёжные состояния требуют проверки billing source.

## Практическая навигация (осмотр 2026-11-16)
[PDF upload form](https://github.com/KriDan-Tech/anki-web-frontend/blob/main/src/app/features/deck/add/pdf-upload-form.ts) — upload/page-selection/quote UI; [extraction page](https://github.com/KriDan-Tech/anki-web-frontend/blob/main/src/app/features/extraction/extraction.page.ts) связывает start, status polling и result presentation. API wrappers, billing and job polling находятся в `src/app`; UI state не означает backend settlement guarantee.

Настройки/версии и клиентские контракты: [README](https://github.com/KriDan-Tech/anki-web-frontend/blob/main/README.md), [package.json](https://github.com/KriDan-Tech/anki-web-frontend/blob/main/package.json), [API verification](https://github.com/KriDan-Tech/anki-web-frontend/blob/main/docs/api-verification.md). Для сценария сверять также [billing service](billing-service.md), [extractor paid contract](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/docs/paid-operation-contract.md) и [gateway API evidence](https://github.com/KriDan-Tech/anki-gen-api-gateway/blob/main/docs/api-verification.md).

## Проверка Task064 — 2026-11-18

После первоначального source-only среза выполнены проверки на `docker-vm`
(`external-docker`): source-service **225 PASS +25 subtests**, 3 opt-in private
OCR tests skipped; frontend **145/145 PASS**; vocab-extractor **300/300 PASS**,
без failures/errors/skips в Java/frontend. Все 6 новых Python и 8 новых Java
page-only проверок исполнились. Миграции source на чистой БД и upgrade с0005
(включая downgrade/повторный upgrade) прошли. Очистка временных контейнеров и
сетей подтверждена. Все три штатных Dockerfile собрали конечные образы.

Это regression/build verification, не deployed или live OCR/AI/E2E acceptance.
Реальные приватные OCR PDF и платные provider calls не выполнялись. Код и тесты
после проверенного снимка не менялись; затем обновлена только документация
результатов. Исторические frozen profiles и `lessons-detect` сохранены.

Подробности: [отчёт](../../task064-verification.md).
