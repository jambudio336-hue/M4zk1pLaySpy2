FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates openssh-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p data/uploads data/builds data/dumps data/keys

EXPOSE 8777
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8777", "--no-access-log"]
