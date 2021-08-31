#!/bin/bash
<< END

    # Diagram of terminology used by this code

    http://elizabeth:opensesame@www.example.com:10000/aa/bb/cc/index.html?key=val#identifier
    └─┬─┘  └───┬───┘ └───┬────┘ └──────┬──────┘└─┬──┘└─────────┬────────┘ └──┬──┘ └───┬────┘
    scheme  username  password        host      port          path          query   fragment
           └─────────┬────────┘ └─────────┬─────────┘└──────────────────┬──────────────────┘
                  userinfo             hostinfo                      pathinfo
           └───────────────────┬────────────────────┘
                           authority
           └───────────────────────────────┬────────────────────────────┘ └───────┬────────┘
                                        hierarchy                              holarchy



END

parse_db() {
    local uri="$1"
    local cmd="$2"

    local scheme=${uri%%:*}; 
    
    local remains=${uri#*:}

    local authority
    if [[ "${remains:0:2}" == "//" ]]; then
        remains="${remains:2}"
        for c in "/" "\?" "\#"; do
            local candidate="${remains%%${c}*}"
            if [[ "$remains" != "$candidate" ]]; then
                local location="${#candidate}"
                authority="${candidate}"
                remains="${remains:location}"
                break
            fi
            authority="$remains"
        done

        local hostinfo userinfo
        if [[ "$authority" == *@* ]]; then
            userinfo="${authority%%\@*}"
            hostinfo="${authority##*\@}"
        else
            hostinfo="$authority"
        fi

        local username password
        if [[ "$userinfo" == *:* ]]; then
            username="${userinfo%%:*}"
            password="${userinfo##*:}"
        fi

        local host port
        if [[ "$hostinfo" == *:* ]]; then
            port="${hostinfo##*:}"
            host="${hostinfo%%:*}"
        else
            host="$hostinfo"
        fi
    fi

    local query
    if [[ "$remains" == *\?* ]]; then
        query="${remains#*\?}"
        remains="${remains%%\?*}"

        local params; declare -A params
        for p in $(tr '&' ' ' <<<"$query"); do
            local param
            IFS='=' read -r -a param <<<"$p"
            params[${param[0]}]=${param[1]}
        done
    fi

    local path
    if [[ "$remains" == */* ]]; then
        path="${remains:1}"
    fi

    local parts
    declare -A parts
    parts=(
        ["scheme"]="$scheme"
        ["host"]="$host"
        ["port"]="$port"
        ["username"]="$username"
        ["password"]="$password"
        ["path"]="$path"
        ["query"]="$query"
    )


    if [[ "${cmd}" == "export" ]]; then
        export URL_AUTHORITY="$authority"
        export URL_USERINFO="$userinfo"
        export URL_HOSTINFO="$hostinfo"
        export URL_HOST="$host"
        export URL_PORT="$port"
        export URL_USERNAME="$username"
        export URL_PASSWORD="$password"
        export URL_PATH="$path"
        export URL_QUERY="$query"
        export URL_PARAM_NAMES="${params[@]}"
        export URL_PARAM_VALUES="${!params[@]}"

    elif [[ "$(type -t $cmd)" == "function" ]]; then
        local parse_db_ctx_parts
        declare -A parse_db_ctx_parts

        for p in "${!parts[@]}"; do
            parse_db_ctx_parts["$p"]="${parts[$p]}"
        done

        $cmd
    elif [[ "${cmd}" == "echo" ]]; then
        echo "\$authority=$authority"
        echo "\$userinfo=$userinfo"
        echo "\$hostinfo=$hostinfo"
        echo "\$host=$host"
        echo "\$port=$port"
        echo "\$username=$username"
        echo "\$password=$password"
        echo "\$path=$path"
        echo "\$query=$query"
        echo "\$param_names=${params[@]}"
        echo "\$param_values=${!params[@]}"
    else
        URL_AUTHORITY="$authority"
        URL_USERINFO="$userinfo"
        URL_HOSTINFO="$hostinfo"
        URL_HOST="$host"
        URL_PORT="$port"
        URL_USERNAME="$username"
        URL_PASSWORD="$password"
        URL_PATH="$path"
        URL_QUERY="$query"
        URL_PARAMS=$params
        URL_PARAM_NAMES="${params[@]}"
        URL_PARAM_VALUES="${!params[@]}"
    fi
}