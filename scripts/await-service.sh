#!/usr/bin/env bash
set -uo pipefail

await_service()
{
    local start_ts=$(date +%s)
    while [ $(date +%s) -lt $((start_ts + $3)) ];
    do
        (echo -n > /dev/tcp/$1/$2) > /dev/null
        if [[ $? -eq 0 ]]; then
            break
        fi
        sleep 1
    done
    local end_ts=$(date +%s)

    if [ $(date +%s) -ge $((start_ts + $3)) ]; then
        echo "Timeout occurred while waiting for $1:$2 to become available"
        exit 1
    fi

    echo "$1:$2 is available after $((end_ts - start_ts)) seconds"
}

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <host> <port> <timeout>"
    exit 1
fi

await_service $1 $2 $3
