#!/bin/bash
set -e
set -x

export PGPASSWORD=firmadyne
export USER=firmadyne

# Start database
echo "firmadyne" | sudo -S service postgresql start
echo "Waiting for DB to start..."
sleep 5

exec "$@"
