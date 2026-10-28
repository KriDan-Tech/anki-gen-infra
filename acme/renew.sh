#!/usr/bin/env bash
# Выпуск и продление сертификата Let's Encrypt на ноде: запускает сервис acme и перезагружает nginx в proxy,
# только если пара certs/tls.{crt,key} изменилась. Вызывается systemd-таймером anki-acme-renew и Ansible (roles/app/tasks/acme.yml).
# Использование: renew.sh [каталог проекта], по умолчанию /srv/myapp.
set -euo pipefail

APP_DIR="${1:-/srv/myapp}"
CRT="$APP_DIR/certs/tls.crt"
COMPOSE=(docker compose --project-directory "$APP_DIR")

before=$(sha256sum "$CRT" 2>/dev/null || true)

# с ненулевым кодом завершается сам запуск lego
"${COMPOSE[@]}" run --rm -T acme

after=$(sha256sum "$CRT" 2>/dev/null || true)

if [ "$before" != "$after" ] && [ -n "$("${COMPOSE[@]}" ps -q proxy)" ]; then
    # при ошибке конфига set -e останавливает скрипт до reload
    "${COMPOSE[@]}" exec -T proxy nginx -t
    "${COMPOSE[@]}" exec -T proxy nginx -s reload
    echo "tls: reloaded"
else
    echo "tls: no change"
fi
