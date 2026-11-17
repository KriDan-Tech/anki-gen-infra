# vocab-extractor

## Назначение и интерфейсы
Планирование кандидатов, AI-разметка заголовков/слов, долговечная работа и передача терминов card-builder. Смотрите focused документы по paid-start и headers, API/AMQP — в `vocab-extractor/README.md`.

## Наблюдаемая реализация (статический срез 2026-11-16)
Осмотрены `vocab-extractor/src/main/java/com/ankigen/vocabextractor/detect/ExtractionRunner.java`, `detect/HeaderProcessingPipeline.java`, `detect/SectionPlanner.java`, `billing/UsageCoordinator.java`, `extraction/PaidStartService.java`, ресурсы Flyway включая `V5__execution_progress.sql` (2026-11-16). Локальная ветка `feat/source-durable-progress-2026-11-16` @bcf8149 с незакоммиченными Task054 изменениями. `vocab-extractor/pom.xml` pin-ит Spring Boot 4.0.0 (Java 21 указан в README); Spring AI version property берётся из того же manifest.

Task058 (статически осмотрено 2026-11-16): `detect/HeadingBatchReconciler.java`,
`detect/HeaderProcessingPipeline.java` и `detect/HeadingSectionPlanner.java`
реализуют page-local abstention после полной согласованной bounded reconciliation.
Несколько независимых retained openings на физической странице исключают все её
заголовки; явные same-opening fragments сохраняются. Integrity errors и конфликт
partition decisions остаются fatal. Существующий full-state CAS атомарно сохраняет
`headingAssemblyPolicy=page-abstention.v1`, `headingAbstentions` с причиной
`MULTIPLE_RETAINED_OPENINGS`/proposal IDs, normalized selections и
`HEADINGS_RESOLVED`; accepted input/catalogue/results/prompts/schemas/digests не
переписываются. Recovery проверяет policy, canonical existing physical pages и
отсутствие confirmed headings на abstained pages. Маркеры сохраняются до
`WORDS_READY`/`PLAN_READY`, но не входят в source word request.

Abstained page, включая unselected context, обрывает наследование предыдущего
тега с начала страницы. Стабильная untagged section
`header-vnext:abstention:<physicalPage>` действует до exact occurrence следующего
confirmed opening; preamble до него тоже без тега. Для context-only страниц не
выдумываются заголовок или OCR offsets. Marker-free resolved states, frozen word
requests и готовые планы не мигрируются; CLOSED операции не открываются заново.
Это наблюдение исходников и synthetic regression sources, не runtime/deployed
подтверждение; task058 сборки/тесты в coding lane не запускались. Подробнее:
[header implementation](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/docs/header-vnext-implementation.md).

## Утверждённая цель
После полного извлечения страницы выбирать верхние слова для AI-заголовков, затем выпускать Draft карточки без этапа предварительного подтверждения. Найденный заголовок переносится до нового; сомнительный/отсутствующий не выдумывать; до первого найденного заголовка — без тега. Номер+название (например `12_Laboratory`) должны сохраняться. Дубликаты проверяются; несколько header tags допустимы; значения и формы go/went/gone сохраняют разные карточки. Ошибки слов/страниц логируются и пропускаются без потери успешного результата.

## Разрывы и неизвестное
Observed pipeline имеет heading-first порядок и выявленные gaps по dedup; `autoConfirm=false` предоставляет review path, не совпадающий с целью immediate Draft. Нынешний finish может завершиться ошибкой при failed/pending pages до term finalization, поэтому нельзя утверждать full partial-result delivery. Финансовая оркестрация сейчас не равна утверждённым start-charge/refund semantics. Критический-error классификатор и частичная финансовая развязка не определены.

## Практическая навигация (осмотр 2026-11-16)
[PaidStartService](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/src/main/java/com/ankigen/vocabextractor/extraction/PaidStartService.java) содержит source/word-list start, cancel и retry-waiting-credits entrypoints; [ExtractionRunner](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/src/main/java/com/ankigen/vocabextractor/detect/ExtractionRunner.java) запускает extraction и heartbeat; [HeaderProcessingPipeline](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/src/main/java/com/ankigen/vocabextractor/detect/HeaderProcessingPipeline.java) связывает source blocks с section plan и выделяет pending/occurrence-conflict исходы. HTTP/event contracts сверять в README и focused docs.

## Task059: versioned layout-assisted heading proposal

Для новых acceptance используется профиль `heading-batches.v2`; frozen v1/v2 профиль проверяется по версии плана при replay. V2 передаёт компактную геометрию только для строк в transmitted ranges (с исходными candidate-relative offsets и видимым пересечением), без дублирования текста/слов внутри layout DTO. Native typography указывается только при наличии, OCR size estimate не выдаётся за PDF typography. Сначала учитывается явный Unit N/`第N課`; одинаковый повторный номер — running marker. Ненумерованное открытие требует совместно верхнего положения, относительного размера и separation. TOC/topic shift, иерархия и body/соседние страницы не являются источником. Вызовы proposal/reconciliation считаются с обогащённым prompt в существующих лимитах; overflow приводит к split или явной ошибке, не усечению.

Это source-level описание, не подтверждение runtime accuracy/provider поведения. Regression test sources добавлены и не запускались.

Настройки/версии: [README](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/README.md), [pom.xml](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/pom.xml), [V5 progress migration](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/src/main/resources/db/migration/V5__execution_progress.sql). Focused: [paid operation contract](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/docs/paid-operation-contract.md), [header implementation](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/docs/header-vnext-implementation.md), [API evidence](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/docs/header-vnext-api-evidence.md), [billing integration](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/main/docs/billing-usage-integration.md).