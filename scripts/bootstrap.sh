#!/usr/bin/env bash
set -eo pipefail

if [[ -n "$KUBERNETES" ]]; then
  source /vault/secrets/secrets.txt
fi

if [ -z "$APP_ENV" ]; then
  echo "Please set APP_ENV"
  exit 1
fi

if [[ $PULL_SECRETS_FROM_VAULT -eq 1 ]]; then
  pip install -i $PYPI_INDEX_URL akatsuki-cli
  akatsuki vault get score-service $APP_ENV -o .env
  source .env
fi

cd /srv/root

# await database availability
/scripts/await-service.sh $READ_DB_HOST $READ_DB_PORT $SERVICE_READINESS_TIMEOUT
/scripts/await-service.sh $WRITE_DB_HOST $WRITE_DB_PORT $SERVICE_READINESS_TIMEOUT

# await redis availability
/scripts/await-service.sh $REDIS_HOST $REDIS_PORT $SERVICE_READINESS_TIMEOUT

# await amqp availability
if [[ $AMQP_PORT != "" ]]; then
  /scripts/await-service.sh $AMQP_HOST $AMQP_PORT $SERVICE_READINESS_TIMEOUT
fi

# run the service
exec /scripts/run-service.sh
