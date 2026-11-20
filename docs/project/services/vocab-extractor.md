# vocab-extractor

## Инфраструктурные метрики (осмотр 2026-11-20)

Infra Ansible provides an optional generic `app_actuator_targets` scrape list for application endpoints, but no vocab-extractor metrics endpoint or target is asserted by this service note. Keep it unset unless the exact deployed endpoint and private routing are independently established. Infra does not add a public route or change service implementation. Static infra docs do not prove deployment or scrapeability.

## Task064 — новые PDF только book/page (2026-11-18)

**Решение владельца:** временно без lesson/header detection для новых PDF.
Текущая цель — полный текст выбранных физических страниц, теги `page::N`
и существующий deck `book::<slug>` (включая untitled). Все утверждения ниже
про новые heading acceptance исторические для header-processing-vNext,
а не default новых загрузок. Ранее accepted quotes/jobs, включая ещё не derived,
не мигрируются. Для page-only исторический PDF нужно загрузить заново.

**Статически реализовано:** `detect/PageOnlyPdf.java` задаёт frozen
`page-only.v1` / `physical-pages.v1`; `extraction/StagedPdf.java` выбирает exact
source version, сохраняя `staged-pdf.v1` и `pdf-whole-operation.v1`.
`PaidPreviewService`, `PaidStartService`, `billing/StagedSourceReconciler`
замораживают и проверяют профиль источника; отсутствие нового поля в historical
canonical означает прежний HeaderVNext. `billing/UsageCoordinator.java` до heading
ветки один раз сохраняет source digest/settings/pagePlan в paid_pdf_execution,
после чего проверяет immutable recovery без live model/config. Quote не меняется.

`detect/Preprocessor.java`, `ExtractionRunner.java`, `DetectService.java`
сохраняют full nonblank block ranges без heading/repeated-edge/page-number
фильтров только этого профиля, обходят HeaderVNext/HeaderProcessingPipeline.
V5 singleton ownership, bounded workers, application fences и physical-page
completion не меняются. Термины получают authoritative row page; inferred
heading/candidate/custom source tags игнорируются только здесь. Word/reading
duplicates объединяют page tags в возрастающем порядке без лимита 10, сохраняя
первый scalar page/context. Card builder/deck bookTag и existing-card skip не менялись.

**Граница:** Java21/Boot4.0.0 manifest проверен; Spring7.0.1/Jackson3.0.2 APIs —
exact cached sources (см. `vocab-extractor/docs/page-only-contract.md`).
Reservation-before-activation, cancel/retry/terminal/CLOSED finality и billing
не менялись. Regression sources написаны, НЕ запускались; static source inspection
не подтверждает runtime/AI accuracy/deploy. Будущие исполнения только docker-vm.


## Метрики — phase 1 (static snapshot 2026-11-20)

Observed source (static inspection, 2026-11-20): `pom.xml` uses the Spring Boot 4.0.0 BOM-managed Micrometer 1.16.0 `micrometer-registry-prometheus`; `application.yml` exposes only `health`, `info`, and `prometheus` over Actuator. Singleton `PipelineMetrics` records counters and durations for `source_load`, `heading_detection`, `plan_build`, `word_extraction`, `result_persist`, and `finish`. Closed label sets are outcomes `success`, `failure`, `lease_lost`, `blocked`; no identifiers, document text, URLs, or provider payload are labels. Source-load, heading-selection/bounded-heading, plan construction, vocabulary-group detection, result transaction, and finish boundaries are timed at their respective call sites. API/version evidence: local Boot 4.0.0 `spring-boot-dependencies` BOM pins Micrometer 1.16.0; Micrometer 1.16.0 core sources confirm Counter/Timer builder, tag, registration, increment and record APIs; Boot 4.0.0 `PrometheusMetricsExportAutoConfiguration` creates `PrometheusMeterRegistry`; Boot 4.0 Actuator endpoint docs confirm `management.endpoints.web.exposure.include`. This static inspection does not establish scrapeability or deployment.



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
[header implementation](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/docs/header-vnext-implementation.md).

## Task063 — один vocabulary request на сегмент (source review 2026-11-17)

Новые acceptance в `detect/HeaderVNext.java`,
`detect/ExtractionPipelineSettings.java` и `extraction/StagedPdf.java`
используют `detect-vocab-v5-single-segment`. `detect/SegmentPlanner.java`
создаёт один durable request на один PreparedSegment; `detect/VocabularyProtocol.java`
проверяет singleton membership и положительный billing attempt token.
`detect/DetectService.java` передаёт только marked text этого сегмента и правила,
без серверных page/segment/section IDs. Закрытый v5 ответ содержит только
`items` с word/reading/readingSource/context; `items:[]` — валидный пустой результат.
`detect/SegmentDetectResponse.java` отклоняет лишние поля, duplicate keys и trailing
JSON; сервер связывает слова с сохранёнными page/segment/tag, не исправляя envelope.

`detect/ExtractionRunner.java` запускает не более четырёх workers на extraction,
сохранённые groups распределяются атомарно через общий AI executor.
Run fencing останавливает новые dispatch; уже выданные HTTP calls не отменяются.
Применение результата, application fence и existing physical-page settlement
остаются в прежней транзакции; страница завершается после всех её сегментов.
Failed/blocked segment не останавливает независимую работу siblings.
Это не меняет существующий gap partial-result delivery в finish.

Явно принятый v4 профиль и сохранённые requests/prompts/options/schema читаются
без миграции; `billing/UsageCoordinator.java` сохраняет принятый vocabulary profile
при выводе staged execution settings. UNKNOWN/IN_FLIGHT остаются blocked,
RECEIVED replay локален, existing authorized retry limits сохранены.
«Один запрос» означает один logical durable request, а не запрет retry этого request.
Нет изменений splitter/header identities, финансовой политики или dependencies.
Подробный контракт и границы доказательств:
[single-segment vocabulary](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/docs/single-segment-vocabulary.md).
Статический осмотр не подтверждает provider accuracy, production replay или deploy.

## Историческая heading-цель (только frozen header profiles; superseded для новых PDF Task064)
После полного извлечения страницы выбирать верхние слова для AI-заголовков, затем выпускать Draft карточки без этапа предварительного подтверждения. Найденный заголовок переносится до нового; сомнительный/отсутствующий не выдумывать; до первого найденного заголовка — без тега. Номер+название (например `12_Laboratory`) должны сохраняться. Дубликаты проверяются; несколько header tags допустимы; значения и формы go/went/gone сохраняют разные карточки. Ошибки слов/страниц логируются и пропускаются без потери успешного результата.

## Разрывы и неизвестное
Observed pipeline имеет heading-first порядок и выявленные gaps по dedup; `autoConfirm=false` предоставляет review path, не совпадающий с целью immediate Draft. Нынешний finish может завершиться ошибкой при failed/pending pages до term finalization, поэтому нельзя утверждать full partial-result delivery. Финансовая оркестрация сейчас не равна утверждённым start-charge/refund semantics. Критический-error классификатор и частичная финансовая развязка не определены.

## Практическая навигация (осмотр 2026-11-16)
[PaidStartService](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/src/main/java/com/ankigen/vocabextractor/extraction/PaidStartService.java) содержит source/word-list start, cancel и retry-waiting-credits entrypoints; [ExtractionRunner](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/src/main/java/com/ankigen/vocabextractor/detect/ExtractionRunner.java) запускает extraction и heartbeat; [HeaderProcessingPipeline](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/src/main/java/com/ankigen/vocabextractor/detect/HeaderProcessingPipeline.java) связывает source blocks с section plan и выделяет pending/occurrence-conflict исходы. HTTP/event contracts сверять в README и focused docs.

Настройки/версии: [README](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/README.md), [pom.xml](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/pom.xml), [V5 progress migration](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/src/main/resources/db/migration/V5__execution_progress.sql). Focused: [paid operation contract](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/docs/paid-operation-contract.md), [header implementation](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/docs/header-vnext-implementation.md), [API evidence](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/docs/header-vnext-api-evidence.md), [billing integration](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/blob/feat/task059-header-layout-evidence/docs/billing-usage-integration.md).

## Task059: versioned layout-assisted heading proposal

Для новых acceptance используется профиль `heading-batches.v2`; frozen v1/v2 профиль проверяется по версии плана при replay. V2 передаёт компактную геометрию только для строк в transmitted ranges (с исходными candidate-relative offsets и видимым пересечением), без дублирования текста/слов внутри layout DTO. Native typography указывается только при наличии, OCR size estimate не выдаётся за PDF typography. Сначала учитывается явный Unit N/`第N課`; одинаковый повторный номер — running marker. Ненумерованное открытие требует совместно верхнего положения, относительного размера и separation. TOC/topic shift, иерархия и body/соседние страницы не являются источником. Вызовы proposal/reconciliation считаются с обогащённым prompt в существующих лимитах; overflow приводит к split или явной ошибке, не усечению.

Это source-level описание, не подтверждение runtime accuracy/provider поведения. Regression test sources добавлены и не запускались.

## Task060 — single semantic decision / nonfatal uncertainty (source review 2026-11-17)

Этот срез supersedes Task058/059 утверждения о новом default v2 и fatal partition
disagreement; их даты и исторический frozen wire contract сохранены.
Осмотрены `detect/HeadingProtocol.java`, `HeaderVNext.java`,
`extraction/StagedPdf.java`, `HeadingBatchPlanner.java`,
`HeadingSingleDecisionPlanner.java`, `HeadingNumberEvidence.java`,
`HeadingBatchReconciler.java`, `HeaderProcessingPipeline.java`,
`HeadingSectionPlanner.java`, `HeadingSelectionService.java`,
`ai/AiInvocationStore.java`; `billing/UsageCoordinator.java` сохраняет accepted
executionSettings/profile без изменений.

Observed source behavior: новые acceptance используют отдельные v3 proposal/reconcile
profiles и v3 catalogue, при этом старые Plan/Catalogue/Request records, v1/v2
serialization, canonical digests, prompts, schemas и boundary generation сохранены.
V3 передаёт только same-page existing upper candidates, полный owned literal,
исходные code-point ranges, nearest candidate boundaries, bounded context counts,
range-scoped layout, policy versions и occurrence-index digest/count.
Один Grounded.id получает один authoritative semantic request или local outcome.
Serialized logical envelope включает conservative framing reserve 1024 code points,
учитывает escaped prompt/instructions/schema/layout,
model/options и существующие completion/output reserves; mandatory overflow —
`CONTEXT_UNREPRESENTABLE`, а не split в несколько votes. Logical-envelope bound
не заявляет точный provider tokenizer/HTTP framing. Existing retry одного
immutable request не является новым semantic vote.

Closed v3 response: retain/reject/abstain + unchanged dependency/proposal IDs;
continuation требует retained same-page predecessor. Все frozen legacy responses
сначала валидируются; schedule не сокращается. Retain/continuation disagreement —
`SEMANTIC_DECISION_CONFLICT`, без majority/first/last/adjudication. Зависимая цепочка
становится uncertain; independent invalid continuation остаётся integrity error.
V2 assembly abstains всю спорную физическую страницу, а независимые страницы
сохраняются. Маркеры содержат MULTIPLE_RETAINED_OPENINGS, SEMANTIC_DECISION_CONFLICT,
SEMANTIC_UNCERTAINTY, CONTEXT_UNREPRESENTABLE или DEPENDENCY_UNCERTAINTY;
recovery проверяет cardinality, page ownership и заново выводит source outcomes,
catalogue binding/coverage/digests без переписывания prompts/результатов.

Literal number policy сохраняет source spelling; Unit/Lesson N и 第N課 поддерживают
Arabic/full-width digits и descending 千/百/十 grammar 1..9999. Unsupported
notation не становится reject. Isolated digit требует title/layout corroboration;
ненумерованный opening — position+relative size+separation. Повтор активного либо
ранее спорного номера не создаёт новый opening и не очищает uncertainty barrier.
Не добавлены OCR correction, sequence/topic/body/TOC inference, hierarchy или geometry.

Existing full-state CAS атомарно пишет `page-abstention.v2`, markers, normalized
selections и HEADINGS_RESOLVED; v1 markers читаются. Build передаёт reason-aware
barriers в direct planner, включая context-only/unselected pages; sparse pages
остаются untagged до exact следующего confirmed independent opening. Marker-free
resolved states и frozen word requests/plans не мигрируются. Journal heading-group,
zero-reasoning и progress classification распознают v3. Usage claim/guard,
financial finality/settlement, dependencies и production не менялись.

**Цель и ограничения:** не терять слова из-за семантического спора и не протягивать
stale tags. Статический diff и authored regressions не доказывают правильность
AI/OCR classification или deployed поведение. Legacy schedule costs сохранены;
v3 ограничивает число semantic requests по grounded proposal, не гарантирует
меньшую стоимость каждого PDF. Нет accuracy guarantees. Tests/build/compiler,
OCR/inference/provider/container execution не выполнялись. Любая будущая
авторизованная runtime-проверка — только ssh docker-vm/external-docker.


### Task060 review clarification — static source inspection 2026-11-17

Номер определяется по тому же native-endpoint-completed view, который затем
используется при normalization; исходные Grounded/literal/request evidence остаются
отдельно. Partial [4,5) внутри native Unit7 после uncertainty barrier не может
превратиться в новое opening при последующем расширении endpoints. Possible numbers
на uncertain странице берутся только из retained или uncertainty-bearing proposals:
definitive reject Unit8 рядом с uncertain Maybe не подавляет independent confirmed
Unit8 следующей страницы. Regression sources добавлены, не запускались.

Legacy golden fixtures — независимая статическая проекция Git baseline
835606c7abab42f0102c4699421eb6753cb72d08, с pinned SHA/provenance; это не результат
current code и не исторический runtime capture. Полная cross-process replay
приёмка остаётся unverified; детали Map.of ordering указаны в fixture README.


### Task060: fragmented number coverage — source-only, 2026-11-17

Identity учитывает совокупность ordered ranges одного candidate/opening: Unit 8
в [0,4) и [5,6) сохраняет номер8, если пропущен только original whitespace.
Аналогично Lesson N и 第N課. На uncertain странице ranges объединяются только
в explicit eligible dependency chain после существующего native completion;
definitive rejects исключаются/обрывают цепочку, independent non-continuations
не объединяются. Поэтому fragmented confirmed/disputed marker не теряет identity
и следующий running Unit8 не снимает barrier. Пропуски non-whitespace и
cross-candidate склейка запрещены. Исходное evidence не переписывается.
Focused regression sources добавлены; runtime/accuracy не проверены, запусков не было.


## Task061 — явная identity reconciliation (статический срез 2026-11-17)

**Наблюдаемая реализация:** новые acceptance в HeaderVNext/StagedPdf используют
heading-batches.v4 / heading-proposal.v4 / heading-reconcile.v4;
headingSelectionVersion остаётся 2. Это supersedes только утверждение Task060
о новом default v3. Осмотрены src/main/java/com/ankigen/vocabextractor/detect/
HeadingProtocol.java, HeadingSingleDecisionPlanner.java, HeadingBatchPlanner.java,
HeaderVNext.java, HeadingBatchReconciler.java, HeaderProcessingPipeline.java,
HeadingSelectionService.java, а также extraction/StagedPdf.java и
ai/AiInvocationStore.java относительно корня vocab-extractor.

V4 reconciliation передаёт TOP-LEVEL proposalId=owned.id (Grounded.id).
Ответ обязан точно вернуть его и dependencyDigest при retain/reject/abstain.
owned.candidateId — identity исходного evidence, previousProposal.id — предшественник,
Request.id вроде s0 — scheduling identity; ни одно не заменяет proposalId,
даже если имеет ту же 64-hex форму. Поле добавляется ДО canonical hashing и
учитывается в serialized logical envelope, включая zero-context fallback.
Schema/instructions proposal и closed response schema могут alias v3; reconcile
instructions v4 явно определяют echo. Неверные IDs/digests, malformed/duplicate
JSON и нарушение closed schema остаются integrity errors: validator не ослаблен,
fallback/repair ID и превращения corruption в semantic abstention нет.

Exact profile/settings/plan/schema/instructions проверяются согласованно;
split/repack передаёт точную proposal version. modern означает v3 OR v4 для
shared single-decision limits/envelope/routing, но не подменяет wire version.
Frozen v1/v2/v3 prompts, schemas, insertion order, canonical hashes/bindings и
сохранённые requests не мигрируют. У frozen v3 не появляется новое поле.
Verify заново выводит bindings/coverage, затем dispatch использует SAVED requests.
Сохраняются strict decision/reduce checks, occurrence audit, same-page evidence,
полные mandatory literals, predecessor/local outcomes, source markers, atomic CAS
и page-abstention. Mandatory overflow остаётся CONTEXT_UNREPRESENTABLE, не split
на votes. V4 распознаётся heading-group/progress; SQL имеет шесть prompt slots
и девять связанных аргументов. Usage/billing/settlement, provider/retry rules,
dependencies, frozen word requests/plans и CLOSED операции не менялись.

**Утверждённая цель:** устранить неоднозначность response identity, не ослабляя
валидатор и не переписывая принятые checkpoints.

**Неизвестное:** это статическая реализация и чтение исходников, не runtime,
accuracy, cross-process replay или deployed подтверждение. Существующие synthetic
test sources сохранены; tests/builds/compiler/inference/provider/container execution
не выполнялись. Коммита/push/deploy не было. Будущие авторизованные проверки —
только docker-vm/external-docker, не host. Узкий контракт и exact-version API
evidence — docs/header-vnext-implementation.md и docs/header-vnext-api-evidence.md
сервисного репозитория.


## Task062 — заголовок первого этапа без повторного подтверждения (source review 2026-11-17)

**Наблюдаемая реализация:** новые acceptance в `detect/HeaderVNext.java` и
`extraction/StagedPdf.java` выбирают planner `confirmed-page-headings.v2`.
`detect/HeadingSectionPlanner.java` включает confirmed opening с начала физической
страницы независимо от occurrence masks основного OCR. Тег применяется и к тексту
до найденного фрагмента заголовка; context-only/пустые страницы не требуют выдуманных
OCR offsets. Uncertainty barriers сохраняются до следующего independent confirmed
opening, для v2 — с начала его страницы. Это supersedes только прежнее требование
exact occurrence для перехода в новый раздел, не семантические правила Task060/061.

`detect/HeadingWordExclusion.java` использует masks только для исключения заголовка
из слов: unique exact spans или консервативные complete-native-word совпадения с
same-page canonical geometry и уникальным владением. Absent/ambiguous совпадения не
отменяют confirmed heading; недостающие символы не восстанавливаются. Неопознаваемые
фрагменты могут остаться во входе лексики. Corrupt identities/ranges и contradictory
exact masks остаются integrity errors. Исходные OCR snapshots не переписываются.

`detect/HeaderProcessingPipeline.java` передаёт frozen planner/evidence во все
пути сборки; PLAN_READY возвращает сохранённые source/plan с проверкой версии.
`billing/UsageCoordinator.java` сохраняет accepted planner при derivation.
`grounded-final-words.v1` сохраняет прежнюю строгую привязку: historical accepted
jobs, word requests, checkpoints и CLOSED операции не мигрируются. AI v4 protocol,
source-service, зависимости и финансовая финальность не меняются.

**Утверждённая цель:** отсутствие или неоднозначность повторного OCR-совпадения
не должны блокировать подтверждённый первым этапом заголовок и остальное извлечение.

**Неизвестное:** изменение локальное, без compiler/tests/build/OCR/provider/deploy;
статический осмотр не подтверждает runtime accuracy или deployed состояние.
Источники: перечисленные файлы и `vocab-extractor/docs/header-vnext-implementation.md`,
`vocab-extractor/docs/header-vnext-api-evidence.md`. Будущие авторизованные прогоны —
только docker-vm.


## Task063 — VM verification (2026-11-18)

Полный Maven verify на docker-vm/external-docker: 291/291 PASS, без
failures/errors/skips; включая три PostgreSQL actual-runner сценария
concurrent projection, atomic rollback/replay и interruption/reclaim/late capture.
Docker image `task063-vocab:r2` успешно собран на том же исходном snapshot.
Независимое статическое ревью — NO FINDINGS. Это supersedes прежние утверждения
о незапущенных тестах для проверенного текущего дерева; не подтверждает качество
реального провайдера, Hibernate persistence context, production replay или deploy.
Источник: vocab-extractor/docs/task063-review-verification.md, final VM acceptance.

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
