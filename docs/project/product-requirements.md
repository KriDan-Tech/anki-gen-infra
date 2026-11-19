# Продуктовые требования (утверждённая цель)

Зафиксировано 2026-11-16 по двум последним решениям в `memory/dev/anki-gen/anki-gen-decisions.md`: первоначальные ответы владельца — Telegram 11200, уточнения — Telegram 11203. Это требования владельца, а не доказательство реализации или релизного объёма. Исторические пункты архитектурного черновика могут быть устаревшими; см. узкие пометки supersession в workspace ARCHITECTURE и pricing.

## Task064 — supersession для НОВЫХ PDF, 2026-11-18

По текущему прямому решению владельца определение уроков/заголовков временно
отключено для новых PDF. `page-only.v1` supersedes прежнюю heading-first цель;
она ниже сохранена только как контракт historical header-processing-vNext.
Новые PDF: staged upload → выбранные physical pages → quote → reserve → activation
→ полный native text/один body OCR только выбранных страниц → V5 vocabulary
→ карточки без предварительного approval. Теги только `page::N` и существующий
`book::<slug>`; дубликаты одного word/reading объединяют все page tags, сохраняя
первый page/context. Custom/inferred lesson tags не используются.
Старые accepted/frozen quotes/jobs/commands, включая ещё не derived, не мигрируются;
для нового пути старый PDF загружается заново. Text/manual insertion без изменений.

Статическая реализация осмотрена в source-service/app/{services,pdf_parser,checkpoints,
staging,routes}.py, vocab-extractor/.../{detect/PageOnlyPdf,billing/UsageCoordinator,
extraction/StagedPdf}.java и web-frontend/src/app/features/deck/add/pdf-upload-form.ts.
Regression sources authored; tests/build/compiler/OCR/inference/provider/deploy не
выполнялись. Source review не является runtime proof; будущие исполнения только
docker-vm. Источник требования — прямое поручение владельца Task064.
Финансовые правила ниже не меняются.

## Пользовательский сценарий и обработка

1. Пользователь загружает PDF, выбирает физические страницы, видит расчёт, оплачивает и ждёт завершения; результат — слова, добавленные в колоду.
2. Со всей выбранной физической страницы извлекать слова без crop/обрезания; вне выбора текст/OCR не выполнять. Для новых PDF уроки/заголовки временно не определяются (Task064).
3. Целевой материал — учебники EN/JA. Неподдерживаемый scan всё равно проходит pipeline, без обещания успешного распознавания. Допускается цветной вход; перевод в grayscale — только опциональная обработка.
4. Новые PDF получают только automatic page::N и book::<slug> tags; heading/lesson/custom source tags не добавлять. Старые heading profiles сохраняют свои frozen contracts без миграции.
5. Проверять дубликаты: для одного word/reading объединять page tags по возрастанию без ручного лимита 10; первый page/context сохранять. Existing cards других extraction пропускать без изменения. Разные значения и формы go/went/gone остаются разными карточками.
6. Обязательны слово, перевод, чтение; контекст желателен, но необязателен.
7. Карточка сразу создаётся в существующем состоянии Draft; пользовательского предварительного подтверждения списка нет.

Каждая ошибка отдельного слова/страницы логируется и пропускается, остальная работа продолжается и сохраняется. Результат частичной обработки выдаётся, а не теряется из-за единичной ошибки. Точный порог критической ошибки, делающей продолжение невозможным, пока не специфицирован.

## Исторический Task062 — только frozen header profiles (2026-11-17)

Решение владельца: подтверждённый на первом этапе заголовок не требует повторного
подтверждения основным OCR. Для новых запусков он задаёт начало урока с начала
своей физической страницы. Отсутствие или неоднозначность совпадения во втором
проходе не отменяет заголовок и не останавливает извлечение. Сопоставление допустимо
только как необязательная подсказка для безопасного исключения заголовочных слов:
неоднозначный фрагмент лучше оставить, чем удалить посторонний текст.
Это не отменяет проверки исходного подтверждения, принадлежности evidence и
семантических барьеров. Сохранённые запуски не переводятся на новую политику
автоматически. Реализацию и границы проверки см. в странице vocab-extractor;
решение само по себе не означает deploy или успешную runtime-проверку.

## Task063 — сегмент как единица AI-извлечения (2026-11-17)

Решение владельца: один logical AI request на сегмент, независимые сегменты
выполняются параллельно. Модель возвращает только слова, чтение и контекст,
без служебных page/segment/section IDs и подтверждений обработки.
Принадлежность результата определяет сервер по сохранённому запросу.
Пустой список слов допустим. Существующие авторизованные retries того же
immutable request сохраняются; старые принятые задания не переводятся на новый
протокол автоматически. Это не меняет стоимость/settlement физических страниц
или цель выдачи частичного результата. Наблюдаемая реализация и границы
проверки описаны в странице vocab-extractor; rollout этим решением не установлен.

## Оплата и наборы

Пользователь подтверждает и оплачивает запуск в UI до обработки; это заменяет прежнюю модель списания после доставки/завершения. Внутренние retry/повторная обработка системы не требуют доплаты. PDF-пакет определяется числом выбранных для обработки физических страниц, а не полным размером файла: 1–10 страниц — 29; 11–99 — 99; 100–299 — 149; 300–400 — 259 внутренних кредитов («звёзд»). Это не Telegram Stars. Перевод слова в словаре бесплатен; добавление слова в колоду стоит 2 внутренних кредита. Историческая provenance цены: ранее утверждённая запись от 2026-10-31 в [реестре цен рабочего пространства](../../../.openclaw/workspace/business/ecb-current-pricing.md); она сохранена как существующая цена, а не установлена заново в решениях 2026-11-16.

Успешное завершение с нулём слов не вызывает автоматического возврата; пользователь при необходимости обращается в поддержку. Распознанная критическая ошибка, завершающая обработку, означает отмену и возврат. Не смешивать с ошибками отдельных страниц/слов, которые следует пропускать. Неопределены классификация критических ошибок, финучёт частичного результата и судьба карточек, уже записанных при критическом завершении. Решение не устанавливает ни обязательное удаление этих карточек, ни запрет на удаление; жизненный цикл остаётся открытым.

## Колода и границы релиза

Ближайшие действия: импорт и удаление; перенос/перемещение карточек между колодами не планируется как ближайшая возможность. Не выводить отсюда детали удаления карточек или каскадов, которые не подтверждены кодом. Повторный экспорт желательно использовать для обновления старых карточек, но это пожелание, не гарантия. Минимальный релизный scope не принят.

## Проверяемый продуктовый путь

Загрузка PDF → выбор страниц → quote → оплата → успешная обработка PDF → слова в колоде. Документ задаёт критерий цели; прохождение пути нужно подтверждать отдельной приёмкой, не статическим обзором кода.

## Task059: наблюдаемое поведение заголовков и границы доказательств

В новой реализации используется отдельный замороженный профиль `heading-batches.v2`; ранее сохранённые планы без layout marker и профили v1 должны оставаться читаемыми без миграции их identity/digest. Для новых принятых запусков явный номер урока/юнита, включая `第N課`, является первичным свидетельством; повтор того же номера рассматривается как running marker/продолжение. Ненумерованное начало оценивается только по верхнему положению, относительному размеру строки и разделению вместе. Используется лишь существующая верхняя четверть; body/соседние страницы, sample слов, TOC и тематический сдвиг не добавляются.

Эта формулировка описывает утверждённую политику, а не точность классификации. Исходники/регрессионные тесты не подтверждают runtime качество, OCR результат или production rollout; регрессионные источники добавлены, но не запускались.

## Task060 — уточнение цели и статический срез 2026-11-17

**Цель:** один grounded heading не получает независимые противоречащие semantic
votes из разных occurrence partitions. При остающейся семантической неопределённости
пропустить сомнительный заголовок/всю физическую страницу, если спор затрагивает
opening или фрагмент названия; продолжить извлечение слов без выдуманного или
унаследованного старого тега. Не выбирать большинство, первый/последний ответ и
не запускать дополнительное adjudication inference.

**Наблюдаемые исходники:** новые acceptance выбирают `heading-batches.v3`;
`HeadingSingleDecisionPlanner` создаёт не более одного semantic request на
`Grounded.id` (либо локальный `CONTEXT_UNREPRESENTABLE`). Полный owned literal
не укорачивается. Все substring occurrences остаются адресуемым индексом с digest,
не отдельными votes; в запросе только same-page upper-candidate context/layout.
`HeadingNumberEvidence` различает Unit/Lesson N, 第N課, Arabic/full-width digits
и ограниченную японскую грамматику; 7 внутри 17/даты/слова не становится номером 7.
INN не исправляется в UNIT. Unsupported notation не означает автоматический reject.
Изолированная цифра требует подтверждающих same-page title/layout; без номера
нужна совокупность position, relative size и separation, а не topic/body/TOC.

Политика `page-abstention.v2` сохраняет причины/ownership вместе с normalized
selections и `HEADINGS_RESOLVED` существующим generation-fenced full-state CAS.
Неопределённая context-only/unselected страница тоже останавливает старый тег;
sparse selected pages остаются без тега до exact следующего independent confirmed
opening. Повтор активного или спорного номера как running marker не снимает barrier.
Невалидные JSON/duplicate keys, ownership, digest/range corruption не превращаются
в semantic skip. Provider/transport pending остаётся pending.

**Legacy и неизвестное:** frozen v1/v2 requests/settings/prompts/digests и уже
resolved marker-free state/wordRequest/WORDS_READY/PLAN_READY не мигрируются.
Pending legacy schedule выполняется полностью; валидное retain/continuation
disagreement теперь даёт `SEMANTIC_DECISION_CONFLICT`, не потерю всех слов.
Цена такого frozen schedule не уменьшается. CLOSED финансовые операции не
переоткрываются. Это source-level изменения и regression sources, не runtime,
OCR/provider accuracy, production rollout или гарантия полного продуктового пути.
Ничего не запускалось; будущая авторизованная проверка — только ssh docker-vm
(external-docker), не OpenClaw host.


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

Подробности: [отчёт](../infra/docs/task064-verification.md).

## Task065 — автоматическое email-уведомление о готовой колоде (2026-11-19)

Утверждённая цель: отдельный notification repository/container, RabbitMQ separate
queue, автоматическое письмо с названием колоды и authenticated ссылкой
`/decks/{deckId}`. Привлекательный русский HTML + plain-text alternative,
без attachment, toggle или historical backfill. Получатель только из verified
enabled Keycloak identity по exact user ID; событие не несёт email/произвольный URL.

Готовность — полная durable delivery карточек, не OCR/extraction/build completion
и не один last marker. Modern manifest с полным numbered coverage и legacy
numbered aggregation порождают одно immutable semantic ready intent на
owner/operation/deck/type (без retry generation). Successful empty/dedup-only
delivery допустима; создание пустой колоды/failed generation не уведомляет.
Финансовые правила/settlement не меняются.

Наблюдаемая source реализация 2026-11-19:
`deck-service/.../messaging/{DeliveryEvidenceStore,LegacyBuildReceiptStore,
DeckReadyOutboxStore,DeckReadyDispatcher}.java`, append-only deck V2,
`notification/src/main/`, `auth-keycloak/provision-notification-directory.py`,
infra Compose/Ansible/targeted DB source.
SMTP I/O вне transactions, stable Message-ID, durable bounded retries,
malformed broker DLQ отдельно от SMTP DEAD jobs. Exactly-once email не обещается.
No tests/build/validation/deploy/provision/send performed; runtime/deployed unknown.
Разрешённые будущие исполнения только docker-vm.
См. [notification](services/notification.md).