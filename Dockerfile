FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY query_google_books_api.py .

ENTRYPOINT ["python", "query_google_books_api.py"]