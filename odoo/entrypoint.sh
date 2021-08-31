#!/bin/bash

set -e

source /usr/local/lib/parse_db_url.sh

parse_db "$DATABASE_URL"

export PGHOST="$URL_HOST"
export PGPORT="$URL_PORT"
export PGUSER="$URL_USERNAME"
export PGPASSWORD="$URL_PASSWORD"
export PG_DB="$URL_PATH"
export PG_SSL_MODE='disable'

export ODOO_ADDONS_PATH="$ODOO_ADDONS_PATH"

if [ "$1" == "odoo" ]; then
    shift
    exec odoo \
        --proxy-mode \
        --db_host="$PGHOST" \
        --db_port="$PGPORT" \
        --db_user="$PGUSER" \
        --db_password="$PGPASSWORD" \
        --database="$PG_DB" \
        --no-database-list \
        --addons-path "$ODOO_ADDONS_PATH" \
        --db_sslmode="$PG_SSL_MODE" "$@"
else
    exec "$@"
fi
