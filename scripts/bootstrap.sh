#!/bin/bash
set -euo pipefail

echo "Waiting for services to become available..."

./scripts/await_service.sh $MYSQL_HOST $MYSQL_PORT $SERVICE_READINESS_TIMEOUT
./scripts/await_service.sh $REDIS_HOST $REDIS_PORT $SERVICE_READINESS_TIMEOUT

exec /app/scripts/run_app.sh