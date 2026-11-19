# Flight Insights

A small portfolio ETL pipeline for observed Changi (`WSSS`) arrivals. Airflow schedules a PySpark job on a local Spark standalone cluster; Spark retrieves OpenSky data, cleans it, and writes directly to BigQuery. Example BigQuery queries show arrival hours, estimated origins, and daily counts.

## Setup

You need Docker Compose, roughly 6 GB of memory available to Docker, an OpenSky account with API client credentials, and a Google Cloud project with billing enabled. OpenSky access and quota depend on your account; consult its [API documentation](https://openskynetwork.github.io/opensky-api/rest.html).

1. Enable the BigQuery API and BigQuery Storage API in your project. Create a BigQuery dataset in your preferred location. Give a service account permission to create BigQuery jobs, create/delete/update tables in the dataset, and write using the Storage Write API (for example BigQuery Job User on the project and BigQuery Data Editor on the dataset).
2. Create a service-account JSON key outside source control. Copy `.env.example` to `.env`; set `GOOGLE_CLOUD_PROJECT`, `BIGQUERY_DATASET`, `OPENSKY_CLIENT_ID`, `OPENSKY_CLIENT_SECRET`, and `GOOGLE_CREDENTIALS_FILE` to the local JSON path. The file must be readable by the container user (UID 50000 by default). Docker mounts it read-only as application default credentials in the driver and worker. Never commit either file.
3. Replace `PROJECT.DATASET` in `sql/schema.sql` with your project and dataset, and execute it in the BigQuery console. The table must exist before a run.
4. Initialize and start:

   ```sh
   docker compose build
   docker compose run --rm airflow-init
   docker compose up -d postgres spark-master spark-worker airflow-webserver airflow-scheduler
   ```

   Airflow is at http://localhost:8080 (local-only default login `admin` / `admin`); Spark master UI is at http://localhost:8081. Change the local Airflow credentials if exposing it. The DAG starts paused; unpause `changi_arrivals_daily` when ready.

The scheduler runs at 06:00 UTC and processes the UTC date two days before that trigger. The machine and Docker must be running; `catchup=False` means missed schedules are not automatically backfilled. In the Airflow UI, trigger a manual run with JSON configuration `{"process_date":"2026-11-15"}` to process or backfill a particular UTC date. Retries retain the same date. The DAG serializes its own runs; do not run separate jobs concurrently for the same date.

To inspect imports and stop the stack:

```sh
docker compose exec airflow-scheduler airflow dags list-import-errors
docker compose down
```

`docker compose down -v` also deletes the local Airflow metadata database. BigQuery data remains in your cloud project.

## Insights and data limitations

Replace the project, dataset, and dates in `sql/insights.sql` and run each query in BigQuery. The date partition is based on `lastSeen` in UTC. Singapore hour is local time, and may fall on the following Singapore calendar date.

OpenSky's airport and arrival estimates derive from observations, not an authoritative airport timetable. `firstSeen` and `lastSeen` are observation times; their difference is not a precise flight duration. Coverage and origins can be missing; late corrections require a rerun, and historical API availability and source publication delays are not guaranteed. Empty, invalid, or failed API responses fail the job instead of erasing existing data. OpenSky may return an incomplete but syntactically valid dataset without a detectable signal; inspect source coverage before relying on results.

Spark writes each batch to a unique expiring BigQuery staging table using the connector's direct Storage Write API. Once validated, a single BigQuery `MERGE` atomically replaces only that UTC day; the staging table is then removed. Stages left after a crash expire after 24 hours. This avoids GCS and avoids overwriting other days, but BigQuery storage, queries, and writes may incur charges.

## Tests

With Python 3.11 and Java 17 installed:

```sh
pip install -e '.[test]'
pytest -q
docker compose config --quiet
```

The tests use local Spark and mocked network/cloud calls. An actual OpenSky/BigQuery run requires your credentials and incurs external usage. To smoke-test standalone Spark after starting services:

```sh
docker compose exec airflow-scheduler spark-submit --master spark://spark-master:7077 --conf spark.driver.host=airflow-scheduler /opt/flight/src/spark_smoke.py
```

Check the Spark master UI for a worker and completed application. This smoke test does not access OpenSky or BigQuery.
