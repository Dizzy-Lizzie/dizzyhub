#!/bin/bash

set -e

source /usr/local/lib/parse_db_url.sh

if [ "$1" == "odoo"]; then
    shift
    exec odoo \
        --proxy-mode \
        --db_host="$PG_HOST" \
        --db_port="$PG_PORT" \
        --db_user="$PG_USER" \
        --db_password="$PG_PASS" \
        --database="$PG_DB" \
        --no-database-list \
        --db_sslmode="$PG_SSL_MODE" "$@"
else
    exec "$@"
fi
