#!/bin/bash
# Targeted notification-only provisioning for fresh AND existing volumes.
# VERIFIED SQL source: PostgreSQL17 documentation, see postgres/README.md.
set -euo pipefail
: "${POSTGRES_USER:?}" "${POSTGRES_DB:?}" "${NOTIFICATION_DB_USER:?}" "${NOTIFICATION_DB_PASSWORD:?}"
case "${NOTIFICATION_DB_USER}" in
 pg_*|public)
  echo "Notification cannot use a PostgreSQL built-in identity" >&2
  exit 1
 ;;
esac
# Never reuse another service/bootstrap identity.
for existing in "${POSTGRES_USER}" "${KEYCLOAK_DB_USER:-}" "${SOURCE_DB_USER:-}" \
 "${EXTRACTOR_DB_USER:-}" "${BUILDER_DB_USER:-}" "${DECK_DB_USER:-}" "${BILLING_SANDBOX_DB_USER:-}"; do
 if [ "${NOTIFICATION_DB_USER}" = "${existing}" ]; then
  echo "Notification requires a dedicated DB role" >&2
  exit 1
 fi
done
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" \
 -v notification_user="${NOTIFICATION_DB_USER}" -v notification_password="${NOTIFICATION_DB_PASSWORD}" <<'SQL'
SELECT EXISTS (
 SELECT FROM pg_roles WHERE rolname=:'notification_user'
 AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls)
) OR EXISTS (
 SELECT FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba
 WHERE r.rolname=:'notification_user' AND d.datname<>'notification_sandbox_db'
) OR EXISTS (
 SELECT FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
 WHERE r.rolname=:'notification_user'
) AS unsafe_role \gset
\if :unsafe_role
 \echo 'Refusing elevated/shared notification role; no automatic repair'
 DO $$ BEGIN RAISE EXCEPTION 'notification provisioning precondition failed'; END; $$;
\endif
SELECT EXISTS (
 SELECT FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba
 WHERE d.datname='notification_sandbox_db' AND r.rolname<>:'notification_user'
) AS wrong_owner \gset
\if :wrong_owner
 \echo 'Existing notification database has unexpected owner; operator action required'
 DO $$ BEGIN RAISE EXCEPTION 'notification provisioning precondition failed'; END; $$;
\endif
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L',
 :'notification_user', :'notification_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname=:'notification_user') \gexec
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'notification_user', :'notification_password') \gexec
SELECT format('CREATE DATABASE notification_sandbox_db OWNER %I', :'notification_user')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='notification_sandbox_db') \gexec
REVOKE ALL ON DATABASE notification_sandbox_db FROM PUBLIC;
SQL