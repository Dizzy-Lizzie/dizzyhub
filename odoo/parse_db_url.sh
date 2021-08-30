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


    if [ "${cmd}" ]; then
        local parse_db_ctx_parts
        declare -A parse_db_ctx_parts

        for p in "${!parts[@]}"; do
            parse_db_ctx_parts["$p"]="${parts[$p]}"
        done

        $cmd
    else
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
    fi
}