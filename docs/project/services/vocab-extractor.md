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
