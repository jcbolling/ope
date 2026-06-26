FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y cron procps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY query_google_books_api.py .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]