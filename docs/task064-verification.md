# Task064 — page-only PDF regression/build verification

Date: 2026-11-18. Execution host: docker-vm / external-docker only.

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

## Evidence and reproducibility

Private local evidence: OpenClaw workspace `reports/task064-validation-20261118/`;
VM run `~/work/task064-validation-20261118/`. Source snapshots were transferred
with SHA256 verification and compared against current code before publication.
JUnit XML independently sums to300 Java tests,0 failures/errors/skips; new
PageOnlyExecutionTest3 and PageOnlyPdfTest5 all passed. Source pytest XML253
includes225 test cases,25 passed subtests and3 skipped private OCR cases.
Frontend completed Vitest summary145 passed. No application fixes were needed.

The original prepared Python image carried PaddlePaddle3.3.0 instead of the
pinned3.2.2: its initial Python results are preliminary, not final acceptance.
A fresh image was built from the deployment image with pytest9.1.1; all pinned
runtime dependencies were checked before the full PostgreSQL rerun. Final source
result:225 passed,3 skipped,25 subtests;542.28s. Fresh and upgrade migrations and
cleanup each exited0. Frontend suite935.25s includes dependency preparation;
Java suite2306.89s includes isolated services/build/cleanup. Its longest existing
recovery class took2108s (previous successful baseline2088s).

SSH temporarily became unavailable during verification and recovered on retry;
existing jobs were inspected and continued, not duplicated. No root cause or
production availability claim is made.

## Deployment Dockerfile gates

- source-service task064-source:r1 — PASS,
  sha256:51ba86ed0fc21b3ecfe6dcb027a6c28761b1c3b847bce3e5afbd565eb45fcd16.
- web-frontend task064-frontend:r1 — PASS,
  sha256:a65718e129c834354d5e1f461e9eaa41d713f8dc4139836709d172a84640f3d1.
- vocab-extractor task064-vocab:r1 — PASS,
  sha256:7ddab31e946e462871a83c5a7318d198567e1570abc9e2fe688d540a9273eea9.

Packaging uses each checked-in Dockerfile; Maven packaging skips execution only
because the separate full verify already executed all300 tests. No deployment,
production mutation/replay, real OCR/inference or live provider calls performed.

## Publication

Target main in source-service, vocab-extractor, web-frontend and infra.
Existing infra feature history is to be fast-forwarded into main, not discarded.
`lessons-detect` remains fa9a5ece925e0307356942730923c6afa88d723c.
Prepared main commits (remote tips are checked separately after push):

- source-service: [141d60e](https://github.com/KriDan-Tech/anki-gen-source-service/commit/141d60e620bc48acc9c864112a68666820fc29bc).
- vocab-extractor: [f258317](https://github.com/KriDan-Tech/anki-gen-vocab-extractor/commit/f258317b4cd0a536d5e7b9af6eb1d711f2b3c5c6).
- web-frontend: [e8c21ea](https://github.com/KriDan-Tech/anki-web-frontend/commit/e8c21ea9617bf1f4aa7e99b0b0fa0ebbe6a0a1fa).

Infra main carries this report and the existing feature documentation history.
