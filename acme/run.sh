#!/bin/sh
# Обёртка lego для сервиса acme (docker-compose.yml): получает или продлевает сертификат Let's Encrypt
# через DNS-01 (Selectel) и ставит пару в ./certs, если она изменилась. Запуск: /bin/sh /acme/run.sh внутри образа goacme/lego.
# Флаги lego v5.5.2 проверены по исходникам тега (cmd/internal/flags/flags.go, cmd/internal/root/process_renew.go).
set -eu

die() {
    echo "acme: $*" >&2
    exit 2
}

# проверка входных данных
[ -n "${PUBLIC_HOST:-}" ] || die "PUBLIC_HOST пуст (задайте в infra/.env)"
case "$PUBLIC_HOST" in
    localhost|*:*) die "PUBLIC_HOST=$PUBLIC_HOST: Let's Encrypt выпускает только на домен, не на localhost и не на IPv6" ;;
esac
if printf '%s' "$PUBLIC_HOST" | grep -Eq '^[0-9.]+$'; then
    die "PUBLIC_HOST=$PUBLIC_HOST: Let's Encrypt выпускает только на домен, не на IP-адрес"
fi
case "$ACME_SERVER" in
    letsencrypt-staging|letsencrypt) ;;
    *) die "ACME_SERVER=$ACME_SERVER: допустимо letsencrypt-staging или letsencrypt" ;;
esac
[ -n "${SELECTELV2_USERNAME:-}" ] || die "SELECTELV2_USERNAME пуст (учётные данные Selectel в infra/.env)"
[ -n "${SELECTELV2_PASSWORD:-}" ] || die "SELECTELV2_PASSWORD пуст (учётные данные Selectel в infra/.env)"
[ -n "${SELECTELV2_ACCOUNT_ID:-}" ] || die "SELECTELV2_ACCOUNT_ID пуст (учётные данные Selectel в infra/.env)"
[ -n "${SELECTELV2_PROJECT_ID:-}" ] || die "SELECTELV2_PROJECT_ID пуст (учётные данные Selectel в infra/.env)"

# имя сертификата: отдельное для staging и прода, чтобы переключение выпускало новый сертификат
CERT_NAME="${PUBLIC_HOST}-${ACME_SERVER}"

# аргументы lego run
set -- run --accept-tos --server "$ACME_SERVER" --dns selectelv2 --path /data \
    --cert.name "$CERT_NAME" --domains "$PUBLIC_HOST"
# ACME_EXTRA_DOMAINS: через пробел; set -f, чтобы шаблоны вроде *.ecb.tonzer.ru не раскрывались по файлам
set -f
for domain in ${ACME_EXTRA_DOMAINS:-}; do
    set -- "$@" --domains "$domain"
done
set +f
[ -z "${ACME_EMAIL:-}" ] || set -- "$@" --email "$ACME_EMAIL"
[ -z "${ACME_DNS_RESOLVERS:-}" ] || set -- "$@" --dns.resolvers "$ACME_DNS_RESOLVERS"
# время запуска задаёт таймер (04:00 МСК), поэтому случайная задержка lego не нужна
set -- "$@" --no-random-sleep --force-cert-domains

/usr/bin/lego "$@"

# установка в активную пару: сначала ключ, затем сертификат (mv внутри одного каталога)
if ! cmp -s "/data/certificates/$CERT_NAME.crt" /certs/tls.crt; then
    install -m 0600 "/data/certificates/$CERT_NAME.key" /certs/.tls.key.tmp
    install -m 0644 "/data/certificates/$CERT_NAME.crt" /certs/.tls.crt.tmp
    mv /certs/.tls.key.tmp /certs/tls.key
    mv /certs/.tls.crt.tmp /certs/tls.crt
    echo "tls: installed $CERT_NAME"
else
    echo "tls: unchanged"
fi
