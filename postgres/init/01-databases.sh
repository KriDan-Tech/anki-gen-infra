#!/bin/bash
# Создаёт по одной базе и роли-владельцу на каждый сервис, пароли берёт из env.
# Запускается ОДИН раз — при первой инициализации пустого каталога данных Postgres
# (механизм /docker-entrypoint-initdb.d). Если базы уже есть — пересоздать можно только
# удалив volume postgres-data (см. postgres/README.md).
set -eo pipefail

create_service_db() {
  local db="$1" user="$2" pass="$3"

  if [ -z "${pass}" ]; then
    echo "WARNING: пустой пароль для роли ${user} (база ${db}). Заполните .env." >&2
  fi

  # Роль (идемпотентно)
  psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
    DO \$do\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${user}') THEN
        CREATE ROLE "${user}" LOGIN PASSWORD '${pass}';
      END IF;
    END
    \$do\$;
EOSQL

  # База (CREATE DATABASE нельзя внутри DO/транзакции, поэтому через createdb с проверкой)
  if ! psql -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" \
        --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" | grep -q 1; then
    createdb --username "${POSTGRES_USER}" --owner "${user}" "${db}"
    echo "created database ${db} owned by ${user}"
  else
    echo "database ${db} already exists — skipping"
  fi
}

create_service_db "keycloak_db"  "${KEYCLOAK_DB_USER}"  "${KEYCLOAK_DB_PASSWORD}"
create_service_db "source_db"    "${SOURCE_DB_USER}"    "${SOURCE_DB_PASSWORD}"
create_service_db "extractor_db" "${EXTRACTOR_DB_USER}" "${EXTRACTOR_DB_PASSWORD}"
create_service_db "builder_db"   "${BUILDER_DB_USER}"   "${BUILDER_DB_PASSWORD}"
create_service_db "deck_db"      "${DECK_DB_USER}"      "${DECK_DB_PASSWORD}"

echo "01-databases.sh: все базы и роли готовы."
