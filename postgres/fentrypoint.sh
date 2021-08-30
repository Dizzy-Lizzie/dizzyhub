#!/bin/bash


source /usr/local/bin/docker-entrypoint.sh

_main "$@"

# rm -r "$PGDATA"
# rm -r "$PGDATA/lost+found"