#!/usr/bin/env bash

#set -x	

ENV_NAME='evan-dev'
ENV_ORG='evan-dev'
ENV_REGION='ewr'
PG_ADMIN_PASSWORD='3ch6kcwjmp'


###### Don't Edit
PG_APP_NAME="postgres-${ENV_NAME}"
ODOO_APP_NAME="odoo-${ENV_NAME}"
ODOO_VOL_NAME="odoo_data"

PROJ_PATH="${PWD}"
ODOO_SRC_PATH="${PROJ_PATH}/odoo"



fly() {
    flyctl "$@"
}

pg_app_exists() {
    fly status "${PG_APP_NAME}"
}

odoo_app_exists() {
    fly status "${ODOO_APP_NAME}";
}

pg_odoo_attached() {
    local pg_users=$(
        fly postgres users list "${PG_APP_NAME}" | 
        tail -n +2 | 
        cut -d " " -f1
    )
    grep -P "${ODOO_APP_NAME//-/_}.*" - <<< "$pg_users"
}

odoo_volume_exists() {
    
    local volumes=$(
        fly volumes list --app "$ODOO_APP_NAME" |
        tail -n +2 |
        cut -d " " -f2
    )
    grep -P "$ODOO_VOL_NAME" <<< "$volumes"
}

ssh_console() {
    fly ssh console \
        --app "$ODOO_APP_NAME" \
        --region "$ENV_REGION"
}


###### Commands

create_cmd() {
    if ! pg_app_exists; then
        fly postgres create \
            --name "${PG_APP_NAME}" \
            --organization "${ENV_ORG}" \
            --password "${PG_ADMIN_PASSWORD}" \
            --region "$ENV_REGION" \
            --vm-size shared-cpu-1x \
            --volume-size 10

        if [ "$?" == 1 ]; then
            exit 1
        fi
    fi


    if ! odoo_app_exists; then
        fly init "${ODOO_APP_NAME}" \
            --nowrite \
            --org "$ENV_ORG"
            # --dockerfile "${PROJ_PATH}/odoo/Dockerfile"
            # --import "${PROJ_PATH}/odoo/fly.toml" \
            # --name "${ODOO_APP_NAME}" \
        if [ "$?" == 1 ]; then
            exit 1
        fi
    fi

    if ! pg_odoo_attached; then
        echo "attaching  app $ODOO_APP_NAME to postgres"
        fly postgres attach \
            --postgres-app "$PG_APP_NAME" \
            --app "$ODOO_APP_NAME"
    fi


    volumes=$(
        fly volumes list --app "$ODOO_APP_NAME" |
        tail -n +2 |
        cut -d " " -f2
    )


    if ! odoo_volume_exists; then
        fly volumes create "$ODOO_VOL_NAME" \
            --app "$ODOO_APP_NAME" \
            --region "$ENV_REGION" \
            --size 10 
    fi

}


deploy_cmd() {
    local missing=()


    if ! pg_app_exists; then
        missing+="Postgress cluster"
    fi

    if ! odoo_app_exists; then
        missing+="Odoo application"
    fi

    if ! pg_odoo_attached; then
        missing+="Odoo to postres attachment"
    fi

    if ! odoo_volume_exists; then
        missing+="Odoo data volume"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing resources for deployment:"
        printf '   * %s\n' "${missing[@]}"
        exit 1
    fi

    fly deploy "${ODOO_SRC_PATH}" \
        --app "$ODOO_APP_NAME" \
        --strategy immediate

}


ssh_console_cmd() {
    ssh_console
}


log_cmd() {
    fly logs --app "$ODOO_APP_NAME"
}

info_cmd() {
    fly info --app "$ODOO_APP_NAME"
}

if ! command -v flyctl; then
    echo "flyctl - fly.io cli command not found"
    exit 1
fi


## parse command arg
while (( "$#" )); do
    case "$1" in
        create)
            shift
            create_cmd
        
        ;;
        deploy)
            shift
            deploy_cmd
        ;;
        ssh)
            shift
            ssh_console_cmd
        ;;
        log)
            shift
            log_cmd
        ;;
        info)
            shift
            info_cmd
        ;;
    esac
done