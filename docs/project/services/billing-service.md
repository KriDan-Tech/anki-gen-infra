# billing-service

## Владение и ссылки
Внутренние кредиты, каталог pricing, резерв/settlement ledger и денежные интеграции. Каталог и миграции — первичный источник фактического поведения; дополнительные pricing/payment документы остаются focused деталями.

## Наблюдаемая реализация (2026-11-16)
Осмотрены `billing-service/src/main/java/com/ankigen/billingservice/usage/UsageService.java`, `usage/PricingCatalogueRepository.java`, миграции `V2__payment_packages.sql`, `V3__default_topup_catalogue.sql`, `V5__administrative_refunds.sql`, `V8__whole_operation_pdf_settlement.sql` (2026-11-16). Локальная ветка `feat/source-durable-progress-2026-11-16` @7524c71; untracked служебные cache/Serena не считать частью реализации. Отдельно различать YooKassa sandbox top-ups, admin refunds, расход PDF и внутренние credits/Stars.

## Утверждённая цель
Тарифы PDF: 1–10 — 29; 11–99 — 99; 100–299 — 149; 300–400 — 259 внутренних кредитов. Оплата инициируется пользователем при запуске, системные retry бесплатны. Успешный zero-word — без автоматического refund. Распознанный critical terminating failure — cancel+refund. Бесплатен dictionary translate, платно добавление в deck. Старую цену слова 2 кредита не трактовать как новое решение.

## Разрывы и неизвестное
Наблюдаемая reserve при старте/later settlement — не доказательство утверждённых start-charge/refund semantics. Quote принятой цены, неизменяемость, резервирование и результат следует описывать по конкретной версии ledger. Не определены критическая классификация, финансовый treatment partial results и уже записанных карточек при отмене. Внутренние credits не Telegram Stars; не смешивать с YooKassa и админским возвратом.

## Практическая навигация (осмотр 2026-11-16)
[UsageService](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/src/main/java/com/ankigen/billingservice/usage/UsageService.java) — facade для quote, reserve, read, page outcome, retry, settlement и PDF settlement, делегирующий ledger/quote components. [PricingCatalogueRepository](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/src/main/java/com/ankigen/billingservice/usage/PricingCatalogueRepository.java) читает active catalogue (PDF bands и action prices); миграции отделяют payment packages, admin refunds и whole-operation settlement.

Настройки/схема: [README](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/README.md), [pom.xml](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/pom.xml), `src/main/resources/db/migration/`. Focused: [pricing catalogue](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/docs/pricing-catalogue.md), [payment packages](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/docs/payment-packages.md), [package API evidence](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/docs/payment-packages-api-evidence.md), [API verification](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/docs/api-verification.md), [admin setup](https://github.com/KriDan-Tech/anki-gen-billing-service/blob/main/docs/billing-admin-setup.md).
