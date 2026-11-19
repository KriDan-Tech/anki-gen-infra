# notification

## Владение и утверждённая цель Task065

Отдельный repository `git@github.com:KriDan-Tech/anki-gen-notification.git`,
container и durable email delivery. Автоматическое русское HTML/plain-text письмо
с названием готовой колоды и authenticated ссылкой /decks/{deckId}.
Нет attachment/toggle/backfill/public send API. Readiness и outbox принадлежат
deck-service; billing/расчёты не меняются.

## Наблюдаемая реализация — source-only, 2026-11-19

Источники: `notification/pom.xml` (Java21/Boot4.0.0),
`Dockerfile`, `src/main/resources/application.yml`,
`db/migration/V1__notification_jobs.sql`,
`src/main/java/com/ankigen/notification/{ReadyInbox,JobStore,DeliveryWorker,
RecipientDirectory,MailDelivery,ReadyTopology,DeckReadyEvent}.java`.

Queue notification.deck.ready.v1 принимает immutable envelope deck.ready.v1.
Strict bounded shape/IDs/length validation; inbox + job commit до broker AUTO ACK.
Event ID и owner/operation/deck/type unique, contradictory replay rejected.
Malformed events после bounded broker retries идут в notification.deck.ready.v1.dlq
через anki.events.dlx; SMTP-exhausted jobs остаются DEAD в БД, это разные механизмы.

PENDING/RETRY/IN_FLIGHT/SENT/SUPPRESSED/DEAD, bounded worker, SKIP LOCKED claims,
random token/lease fencing, crash recovery, persisted attempts/backoff/jitter,
stable Message-ID, sanitized diagnostics, ambiguous-attempt flag.
Keycloak exact-ID lookup через отдельный read-only notification-directory;
только enabled/emailVerified/single mailbox. Deleted/ineligible suppression,
bounded operational retries без recipient fallback. Token-only cache, user
обновляется на каждой send attempt, 32KiB response cap, connect/read timeouts.

Shared SMTP_HOST/PORT/TLS_MODE/USERNAME/PASSWORD/FROM/FROM_NAME:
external starttls(required) или implicit tls, normal certificate/hostname validation,
finite timeouts; partial config fail. Все пусты → internal Mailpit1025 no auth/TLS.
Inline email CSS/HTML escaping + text alternative, configured trusted HTTPS origin.
Допустимые embedded newline/control в имени принимаются без изменения immutable
payload; whitespace/control нормализуется только в email rendering. Pre-send SMTP
AUTH failures сохраняют sanitized smtp_auth и retry до общего attempt limit без
новой ambiguity; постоянные SMTP5xx — DEAD.
SENT только после SMTP success; DB commit crash после acceptance может
дублировать письмо, stable Message-ID не даёт exactly-once.

## Эксплуатация и неизвестное

No build/tests/validation/deploy/live provisioning/email. Runtime/deployed state
не подтверждено. Future separately authorized execution — только docker-vm.
Fresh/existing notification DB provisioning до app startup описан в infra;
controller private-repo access обязателен. Dedicated Keycloak provisioner —
отдельное operator действие, bootstrap credential не попадает в notification.
Known deployed deck V1 checksum/schema mismatch — prerequisite перед deck V2.
Legacy batches до tracking не backfill'ятся и не доказывают completion.

Нужны independent docker-vm compile/regression/concurrency/rollback/broker/TLS/MIME
checks; remaining exact-declaration gaps перечислены в
[API evidence](../../notification/docs/api-verification.md).
Полный эксплуатационный контракт: [notification README](../../notification/README.md).
Смежные владельцы: [deck](deck-service.md), [auth](auth-keycloak.md), [infra](infra.md).