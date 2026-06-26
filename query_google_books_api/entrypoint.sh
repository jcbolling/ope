#!/bin/sh
set -e

echo "$CRON_SCHEDULE GOOGLE_BOOKS_API_KEY=$GOOGLE_BOOKS_API_KEY /usr/local/bin/python3 /app/query_google_books_api.py '$SEARCH_TERM' $MAX_RESULTS >> /proc/1/fd/1 2>> /proc/1/fd/2" > /tmp/crontab

crontab /tmp/crontab

echo "Starting cron with schedule: $CRON_SCHEDULE"
exec cron -f -L /dev/stdout