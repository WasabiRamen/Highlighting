FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       libssl-dev \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the project
COPY . /app

# Ensure keys dir exists (mounted by compose for persistence)
RUN mkdir -p /app/keys

EXPOSE 8000 50051

# On container start, generate master key only if it doesn't exist, then start the service
CMD ["/bin/bash", "-lc", "mkdir -p /app/keys && if [ ! -f /app/keys/master.key ]; then python mkgen/mkgen.py --path /app/keys/master.key; fi && ./service_start.sh"]
