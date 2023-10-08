#!/usr/bin/env bash
set -euo pipefail

if [ "$CODE_HOTRELOAD" == "true" ]; then
  EXTRA_ARGUMENTS="--reload"
else
  EXTRA_ARGUMENTS=""
fi

exec uvicorn app.init_api:asgi_app \
  --port $APP_PORT \
  $EXTRA_ARGUMENTS
