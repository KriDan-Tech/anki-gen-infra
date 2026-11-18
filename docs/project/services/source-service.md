# source-service

## Task064 — текущая цель новых PDF (2026-11-18)

**Решение владельца:** временно убрать определение уроков/заголовков для НОВЫХ
PDF. Новый frontend загружает `processingVersion=page-only.v1`, `staged=true`.
Это supersedes прежнюю heading-first цель ниже только для новых загрузок.
Исторические header-processing-vNext sources/quotes/jobs сохраняют точный профиль;
автоматического преобразования нет — для нового пути PDF загружается заново.

**Наблюдаемая реализация, только статическое чтение:** `app/routes.py`,
`services.py`, `staging.py`, `pdf_parser.py`, `checkpoints.py`: staging считает
страницы и сохраняет файл, но не распознаёт текст. После immutable activation
обрабатываются только выбранные сортированные физические страницы (например 2,9),
целиком: native text либо один full-page OCR через существующий
`recognize_full_page(...purpose="word_extraction")`. Нет upper candidates,
header retry/recovery, heading masks или повторного body OCR. Метаданные общего
числа страниц не являются распознаванием. Исходные номера страниц сохраняются,
block indices непрерывны по выбранной последовательности. Empty page сохраняется.

Identity/phase `page-only-body.v1` отдельно связывает owner/source/file/language,
выбор страниц и recognition settings; upperFraction/upperLineLayout не входят.
Resume допускает лишь prefix выбранной последовательности. Finalization сравнивает
body payloads с committed page checkpoints; progress total равен числу выбранных
страниц, stage — page_processing. Historical serialization без миграции.

**Неизвестное:** это статически реализовано, НЕ runtime/OCR/deploy verified.
Regression sources `tests/test_page_only.py` написаны, не запускались.
Pins проверены в `pyproject.toml`: Python>=3.12, SQLAlchemy2.1.6,
pdfplumber0.11.10, PaddleOCR3.7.0, PaddlePaddle3.2.2. API evidence:
`docs/header-vnext-api-evidence.md`. Будущие авторизованные прогоны только docker-vm.


## Назначение и владение
Приём PDF, физические страницы, текст/геометрия, OCR и долговечное хранение входа/результатов до разрешённой стадии удаления. Vocab-extractor — потребитель извлечённых страниц. Подробности API — в `source-service/README.md`; focused OCR layout/API evidence — в документах сервиса.

## Наблюдаемая реализация (статический срез 2026-11-16)
Осмотрены `source-service/app/routes.py`, `services.py`, `pdf_parser.py`, `header_candidates.py`, `header_words.py`, `word_jobs.py`, `checkpoints.py`, `durable_files.py`, `pdf_geometry.py`, `source-service/alembic/versions/` и `source-service/pyproject.toml` (2026-11-16). `header_candidates.py` описывает strict displayed upper-quarter crop, без full-page fallback; `routes.py` принимает pageFrom/pageTo; checkpoint/durable code содержит fenced state и pending-commit marker. Для OCR/runtime dependency versions source-of-truth — pin manifest; PaddleOCR 3.7.0 и PaddlePaddle 3.2.2 указаны в зафиксированном источнике/решении 2026-11-16. Локальная ветка на момент осмотра `feat/source-durable-progress-2026-11-16` @4484125 с незакоммиченными Task054 файлами; root polyrepo не имеет пригодной общей git-истории.

## Историческая heading-цель (только frozen header profiles; superseded для новых PDF Task064)
Обрабатывать полностью каждую выбранную страницу без cropping текста; после извлечения выбирать верхние слова и передавать их на определение заголовков AI; затем карточки учитывают заголовки. EN/JA, цвет допустим, grayscale optional. Ошибки отдельных страниц/слов логировать, пропускать и сохранять остальной результат; scan не отклонять заранее как неподдерживаемый. Границы выбора страниц обязательны.

## Разрывы и неизвестное
Текущая vNext-логика строгого crop верхней четверти для кандидатов отличается от цели full-page extraction; не путать её с legacy parsing. Документация OCR-LAYOUT/API и реализация описывают текущие слои, но статический код не доказывает OCR-качество. Без evidence не утверждать безопасный fallback для отсутствующего заголовка. Task054 durable/checkpoint изменения в рабочем дереве — не HEAD и не runtime proof. Ошибки geometry/occurrence и сохранение partial output требуют приёмки. Удаление исходников при завершении проверять по реальному lifecycle, не обещать по общему README.

## Практическая навигация (осмотр 2026-11-16)
[Upload entrypoint](../../source-service/app/routes.py) принимает multipart PDF, EN/JA, tags и `pageFrom/pageTo`, создаёт source и возвращает 202; там же list/get и internal parsed-block handoff для extractor. [services.py](../../source-service/app/services.py) координирует parse lifecycle, [checkpoints.py](../../source-service/app/checkpoints.py) — parse/word identity and checkpoint invariants, [durable_files.py](../../source-service/app/durable_files.py) — публикацию/проверку файла и неопределённый commit marker. [header_candidates.py](../../source-service/app/header_candidates.py) описывает vNext strict upper-quarter OCR crop без full-page fallback.

Настройки/версии: [README](../../source-service/README.md), [pyproject.toml](../../source-service/pyproject.toml). Контрактные детали: [API verification](../../source-service/docs/api-verification.md), [header vNext evidence](../../source-service/docs/header-vnext-api-evidence.md).

## Task059: layout evidence policy marker

Новый upper-header parse может замораживать `upper-line-layout.v1` в parse identity. Legacy identity без marker остаётся без него; committed page manifests не обогащаются на месте. В рамках нового профиля native pdfplumber line typography хранится отдельно от OCR size estimate; старые word identities и извлечение слов не меняются. Это статически наблюдаемая реализация, не подтверждение OCR/runtime качества. Regression source добавлен и не запускался.


## Task062 — occurrence evidence больше не является обязательным подтверждением (2026-11-17)

Изменение находится только в потребителе vocab-extractor: новый planner
`confirmed-page-headings.v2` принимает заголовок первого этапа как page-level
boundary. Source-service продолжает отдавать независимый основной OCR, native
words/geometry и occurrence diagnostics; `app/header_words.py`, word-job/request
identities и checkpoints этой задачей не менялись. Absent/ambiguous masks не
переписываются в exact и недостающие символы не синтезируются. Для нового planner
это необязательное evidence исключения заголовка из лексики, а не второй голос.
Frozen `grounded-final-words.v1` в extractor сохраняет прежнее поведение.
Подробности и ограничения — [vocab-extractor](vocab-extractor.md), Task062.
Это статическое описание контракта потребления, не проверка OCR/runtime/deploy.

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
