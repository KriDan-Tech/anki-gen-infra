# web-frontend

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
