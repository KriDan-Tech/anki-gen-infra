# deck-service

## Владение
Пользовательские deck/card записи, теги, review и экспорт Anki package. См. README сервиса для API и focused export notes для формата.

## Наблюдаемая реализация (статический срез 2026-11-16)
Осмотрены `deck-service/src/main/java/com/ankigen/deckservice/deck/DeckService.java`, `messaging/CardsBuiltListener.java`, `export/ExportService.java`, `export/ExportWorker.java`, `src/main/resources/db/migration/V1__init.sql` (2026-11-16). Локальная ветка `main` @159f63e. `deck-service/pom.xml` pin-ит Spring Boot 4.0.0 (Java 21 указан в README). Рядом есть незакоммиченные служебные каталоги .serena — статус чистоты не заявляется.

## Утверждённая цель
Термины после обработки сразу создают Draft карточки; повторяющиеся слова проверяются, несколько тегов допустимы, разные meanings и словоформы сохраняются отдельно. Импорт и удаление относятся к ближайшим пожеланиям, но конкретный scope API/каскадов не следует из этого документа. Обновление старых карточек повторным экспортом — preference, не продуктовая гарантия.

## Разрывы и неизвестное
Текущая модель/dedup/export может не совпадать с нужной идентичностью карточки; сверяйте конкретную entity и constraints. Не обещать импорт, delete semantics или upsert при повторном экспорте без inspected source. Удаление карточек при критической отмене extraction не утверждено.

## Практическая навигация (осмотр 2026-11-16)
[CardsBuiltListener](../../deck-service/src/main/java/com/ankigen/deckservice/messaging/CardsBuiltListener.java) принимает card-builder result; [DeckService](../../deck-service/src/main/java/com/ankigen/deckservice/deck/DeckService.java) владеет deck operations; [ExportService](../../deck-service/src/main/java/com/ankigen/deckservice/export/ExportService.java) и [ExportWorker](../../deck-service/src/main/java/com/ankigen/deckservice/export/ExportWorker.java) ведут запрос и background export. Прослеживать повторный export по этим слоям, не выводя upsert-гарантию из пожелания.

Настройки/схема: [README](../../deck-service/README.md), [pom.xml](../../deck-service/pom.xml), [migration V1](../../deck-service/src/main/resources/db/migration/V1__init.sql). Контракт: [API verification](../../deck-service/docs/api-verification.md).

## Task065 — статически написанная реализация, 2026-11-19

Источники: `deck-service/src/main/java/com/ankigen/deckservice/messaging/`
(`DeliveryEvidenceStore`, `CardsBuiltListener`, новые `DeckReadyEvent`,
`DeckReadyOutboxStore`, `DeckReadyDispatcher`, `LegacyBuildReceiptStore`,
`ReadyTopology`), `src/main/resources/db/migration/V2__deck_ready_notification.sql`,
`application.yml`, `DeckServiceApplication.java`.

Modern completeManifest после всех numbered durable receipts в одной transaction
с cards/evidence создаёт notification outbox intent. Locked persisted Deck задаёт
owner/name. Generation fencing/ownership/fingerprints не обходятся.
Legacy durable identity/batches/terminal count должны доказать 1..N; pre-cutover
batches не backfill'ятся. Deleted-deck legacy skip сохранён.
Semantic owner/operation/deck/type без generation не меняет старый envelope при retry.
Bounded SKIP LOCKED claims, token/lease fencing, network вне transaction;
persistent event со stable ID, correlated ACK + no mandatory return.
Queue `notification.deck.ready.v1`, routing `deck.ready.v1`, DLX/DLQ как в
[notification](notification.md).

Утверждённая цель Task065: automatic ready email, не OCR/build-completed email.
Пустой deck не уведомляет; successful empty/dedup delivery может уведомить.
Billing не меняется. Unknowns: compile/runtime/concurrency/broker behavior ещё не
проверялись; существующий deployed V1 history/schema mismatch — обязательный
отдельный operator prerequisite перед V2. V1 не переписан, auto repair не добавлен.