FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY init_db.py .

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/savings_goals.db

EXPOSE 6003

CMD ["sh", "-c", "if [ ! -f \"$DB_PATH\" ]; then python init_db.py; fi && exec python app.py"]