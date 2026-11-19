FROM apache/airflow:2.10.5-python3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir 'apache-airflow==2.10.5' pyspark==3.5.5 requests 'google-cloud-bigquery>=3.25,<4'
ENV SPARK_HOME=/home/airflow/.local/lib/python3.11/site-packages/pyspark \
    PATH=/home/airflow/.local/lib/python3.11/site-packages/pyspark/bin:$PATH \
    PYTHONPATH=/opt/flight/src \
    PYSPARK_PYTHON=python3
