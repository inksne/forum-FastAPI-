FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
<<<<<<< HEAD
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
=======
    build-essential && rm -rf /var/lib/apt/lists/*
>>>>>>> 80a2df1d61926522f78e1a6921ba26970a10d7a7

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 10000