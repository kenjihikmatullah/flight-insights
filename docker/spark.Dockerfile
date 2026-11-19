FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyspark==3.5.5 requests 'google-cloud-bigquery>=3.25,<4'
ENV SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark \
    PYTHONPATH=/opt/flight/src \
    PYSPARK_PYTHON=python3
