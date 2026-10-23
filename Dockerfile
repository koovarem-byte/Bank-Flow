FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Health-сервер и Mini App слушают PORT (по умолчанию 10000)
EXPOSE 10000

CMD ["python", "main.py"]
