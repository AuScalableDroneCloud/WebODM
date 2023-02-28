#!/bin/bash
#(todo, move to loadenv.sh or similar)
SECRET_ENV_FILE=${__dirname}/.env.secret
if test -f "$SECRET_ENV_FILE"; then
    echo "Using secret variables from $SECRET_ENV_FILE"
    source "$SECRET_ENV_FILE"
else
    echo "ERROR: $SECRET_ENV_FILE does not exist, please create it before running in production"
fi
export WO_AUTH0_SECRET="$WO_AUTH0_SECRET"

export WO_AUTH0_KEY="$WO_AUTH0_KEY"
export WO_AUTH0_DOMAIN="$WO_AUTH0_DOMAIN"

export WO_ENCRYPTION_KEY="$WO_ENCRYPTION_KEY"


