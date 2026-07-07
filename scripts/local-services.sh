#!/usr/bin/env bash
# Starts/stops the local (no-sudo, no-docker) Postgres + Redis used for
# Phase 1 dev/testing — see .local-services/ and appPlan.txt DEVELOPMENT
# ENVIRONMENT. Not a substitute for docker-compose in CI/prod, just a fast
# local loop while iterating.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SVC="$ROOT/.local-services"
PG_BIN="$SVC/postgres/pg_local/usr/lib/postgresql/16/bin"
PG_LIB="$SVC/postgres/pg_local/usr/lib/x86_64-linux-gnu"
PG_DATA="$SVC/postgres/pgdata"
PG_SOCKDIR="/tmp/trackify_pgsock"
PG_PORT=5433
REDIS_BIN="$SVC/redis"
REDIS_PORT=6380

export LD_LIBRARY_PATH="$PG_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

start() {
  mkdir -p "$PG_SOCKDIR"
  if "$PG_BIN/pg_ctl" -D "$PG_DATA" status >/dev/null 2>&1; then
    echo "postgres already running"
  else
    "$PG_BIN/pg_ctl" -D "$PG_DATA" -l "$SVC/postgres/pg.log" \
      -o "-p $PG_PORT -k $PG_SOCKDIR -c listen_addresses='127.0.0.1'" start
  fi

  if "$REDIS_BIN/redis-cli" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
    echo "redis already running"
  else
    "$REDIS_BIN/redis-server" --port "$REDIS_PORT" --daemonize yes \
      --logfile "$SVC/redis/redis.log" --dir "$SVC/redis"
  fi
  echo "postgres on 127.0.0.1:$PG_PORT, redis on 127.0.0.1:$REDIS_PORT"
}

stop() {
  "$PG_BIN/pg_ctl" -D "$PG_DATA" stop -m fast || true
  "$REDIS_BIN/redis-cli" -p "$REDIS_PORT" shutdown nosave || true
}

status() {
  "$PG_BIN/pg_ctl" -D "$PG_DATA" status || true
  "$REDIS_BIN/redis-cli" -p "$REDIS_PORT" ping || true
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) echo "usage: $0 {start|stop|status}" >&2; exit 1 ;;
esac
