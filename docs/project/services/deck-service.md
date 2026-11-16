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
[CardsBuiltListener](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/src/main/java/com/ankigen/deckservice/messaging/CardsBuiltListener.java) принимает card-builder result; [DeckService](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/src/main/java/com/ankigen/deckservice/deck/DeckService.java) владеет deck operations; [ExportService](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/src/main/java/com/ankigen/deckservice/export/ExportService.java) и [ExportWorker](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/src/main/java/com/ankigen/deckservice/export/ExportWorker.java) ведут запрос и background export. Прослеживать повторный export по этим слоям, не выводя upsert-гарантию из пожелания.

Настройки/схема: [README](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/README.md), [pom.xml](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/pom.xml), [migration V1](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/src/main/resources/db/migration/V1__init.sql). Контракт: [API verification](https://github.com/KriDan-Tech/anki-gen-deck-service/blob/main/docs/api-verification.md).
