#!/usr/bin/env bash
set -e

export PGPASSWORD="$POSTGRES_PASSWORD"
export PGHOST="db"
export PGPORT="5432"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"

until pg_isready > /dev/null 2>&1; do
  echo "Waiting for Postgres at $PGHOST:$PGPORT (db=$PGDATABASE)…"
  sleep 1
done

if [ "${APPLY_MIGRATIONS:-1}" = "1" ]; then
  echo "Applying migrations..."
  alembic -c /app/alembic.ini upgrade head
else
  echo "Skipping migrations (APPLY_MIGRATIONS=$APPLY_MIGRATIONS)"
fi

exec python -m random_coffee_bot.main