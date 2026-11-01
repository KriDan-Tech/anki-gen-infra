#!/bin/bash
# Создаёт по одной базе и роли-владельцу на каждый сервис, пароли берёт из env.
# Запускается ОДИН раз — при первой инициализации пустого каталога данных Postgres
# (механизм /docker-entrypoint-initdb.d). Уже существующий volume не запустит этот init-скрипт
# повторно; для добавления базы в него volume удалять не нужно (см. postgres/README.md).
set -eo pipefail

create_service_db() {
  local db="$1" user="$2" pass="$3"

  if [ -z "${pass}" ]; then
    echo "WARNING: пустой пароль для роли ${user} (база ${db}). Заполните .env." >&2
  fi

  # Роль (идемпотентно)
  psql -v ON_ERROR_STOP=1 -v db_user="${user}" -v db_password="${pass}" \
    --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<'EOSQL'
    SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'db_user', :'db_password')
    WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'db_user')
    \gexec
EOSQL

  # База (CREATE DATABASE нельзя внутри DO/транзакции, поэтому выполняем через psql \gexec)
  local db_exists
  db_exists=$(psql -tA -v db="${db}" --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<'EOSQL'
    SELECT EXISTS (SELECT FROM pg_database WHERE datname = :'db')
EOSQL
  )
  if [ "${db_exists}" != "t" ]; then
    psql -v ON_ERROR_STOP=1 -v db_name="${db}" -v db_owner="${user}" --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<'EOSQL'
      SELECT format('CREATE DATABASE %I OWNER %I', :'db_name', :'db_owner')
      WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db_name')
      \gexec
EOSQL
    echo "created database ${db} owned by ${user}"
  else
    echo "database ${db} already exists — skipping"
  fi
}

create_service_db "keycloak_db"  "${KEYCLOAK_DB_USER}"  "${KEYCLOAK_DB_PASSWORD}"
create_service_db "source_sandbox_db"    "${SOURCE_DB_USER}"    "${SOURCE_DB_PASSWORD}"
create_service_db "extractor_sandbox_db" "${EXTRACTOR_DB_USER}" "${EXTRACTOR_DB_PASSWORD}"
create_service_db "builder_sandbox_db"   "${BUILDER_DB_USER}"   "${BUILDER_DB_PASSWORD}"
create_service_db "deck_sandbox_db"      "${DECK_DB_USER}"      "${DECK_DB_PASSWORD}"
create_service_db "billing_sandbox_db"  "${BILLING_SANDBOX_DB_USER}" "${BILLING_SANDBOX_DB_PASSWORD}"

echo "01-databases.sh: все базы и роли готовы."