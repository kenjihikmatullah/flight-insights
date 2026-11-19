"""Daily standalone Spark job; manual runs require a process_date."""

import subprocess
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator

from flight_insights.job import process_date


def submit(**context):
    dag_run = context["dag_run"]
    # Airflow logical_date is the start of the data interval. Its end is the
    # scheduled trigger time for a daily cron timetable.
    day = process_date(dag_run.run_type, context["data_interval_end"], dag_run.conf or {})
    subprocess.run([
        "spark-submit", "--master", "spark://spark-master:7077", "--deploy-mode", "client",
        "--conf", "spark.driver.host=airflow-scheduler",
        "--conf", "spark.executorEnv.PYTHONPATH=/opt/flight/src",
        "--conf", "spark.executorEnv.GOOGLE_APPLICATION_CREDENTIALS=/opt/credentials/google.json",
        "--packages", "com.google.cloud.spark:spark-3.5-bigquery:0.46.1",
        "--exclude-packages", "com.google.cloud.spark:spark-bigquery-connector-common,com.google.cloud.spark:spark-bigquery-dsv2-common",
        "/opt/flight/src/spark_job.py", "--date", day.isoformat(),
    ], check=True)


with DAG(
    dag_id="changi_arrivals_daily", start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule="0 6 * * *", catchup=False, max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=10)},
) as dag:
    PythonOperator(task_id="submit_arrivals", python_callable=submit)
