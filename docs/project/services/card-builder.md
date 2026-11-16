# card-builder

## Владение и граница
Перевод/чтение термина и построение карточечного payload; локальный словарь переводов, не владелец пользовательской колоды. API/конфигурация — в `card-builder/README.md` и focused dictionary docs.

## Наблюдаемая реализация (2026-11-16, статическое чтение)
Осмотрены `card-builder/src/main/java/com/ankigen/cardbuilder/build/BuildService.java`, `translation/TranslationService.java`, `translation/TranslationProvider.java`, `dictionary/LocalWord.java`, `src/main/resources/db/migration/V2__durable_build_publication.sql` (2026-11-16). Локальный HEAD `feat/task045-ui-dictionary-2026-11-14` @63c4604. `card-builder/pom.xml` pin-ит Spring Boot 4.0.0 (Java 21 указан в README); Spring AI version property — в manifest. Рядом существуют focused источники API/provider; именно они определяют pinned API.

## Утверждённая цель
Обязательные поля карточки: слово, перевод, чтение; контекст опционален. Разные значения одного написания/чтения — отдельные карточки; go/went/gone не лемматизировать. Идентичность и дедуп должны учитывать эти требования, сохраняя multiple heading tags. Черновик попадает в колоду без предварительного user approval.

## Разрывы и неизвестное
Наблюдаемое nullable translation/reading и fallback `NEEDS_REVIEW` отличаются от обязательных полей цели. Текущая идентичность/дедуп не должна считаться соответствующей различным meanings без проверки. Outbox и event доставка — не гарантия сохранности сквозного сценария. Не утверждать import/re-export update поведение без соответствующего source.

## Практическая навигация (осмотр 2026-11-16)
[BuildService](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/src/main/java/com/ankigen/cardbuilder/build/BuildService.java) принимает подтверждённый terms payload, координирует translation/build lifecycle и recovery claims. [TranslationService](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/src/main/java/com/ankigen/cardbuilder/translation/TranslationService.java) отвечает за переводочный flow через [TranslationProvider](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/src/main/java/com/ankigen/cardbuilder/translation/TranslationProvider.java); [LocalWord](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/src/main/java/com/ankigen/cardbuilder/dictionary/LocalWord.java) — persisted dictionary model. Публикация результата проходит durable outbox path, поэтому для доставки следует проследить event contract, а не предполагать синхронную запись deck.

Настройки/схема: [README](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/README.md), [pom.xml](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/pom.xml), [migration V2](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/src/main/resources/db/migration/V2__durable_build_publication.sql). Focused: [API verification](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/docs/api-verification.md), [delivery evidence contract](https://github.com/KriDan-Tech/anki-gen-card-builder/blob/main/docs/delivery-evidence-contract.md).
