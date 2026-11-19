# Flight Insights

A small ETL pipeline that collects observed arrivals at Singapore Changi (`WSSS`) from OpenSky, processes them with PySpark, and stores daily results in BigQuery.

## Setup

You need Docker Compose, OpenSky API credentials, and a Google Cloud project with BigQuery and BigQuery Storage APIs enabled. Create a BigQuery dataset and a service account with permission to write to it.

1. Copy `.env.example` to `.env` and fill in the OpenSky client ID and secret, Google Cloud project, dataset, and path to your service-account JSON key (`GOOGLE_CREDENTIALS_FILE`). Keep `.env` and credential files private; never commit them.
2. Create the table by setting the project and dataset in `sql/schema.sql`, then run that SQL in BigQuery.
3. Build and start the services:

   ```sh
   docker compose build
   docker compose run --rm airflow-init
   docker compose up -d postgres spark-master spark-worker airflow-webserver airflow-scheduler
   ```

Airflow is at [http://localhost:8080](http://localhost:8080) (default local login: `admin` / `admin`). Spark's UI is at [http://localhost:8081](http://localhost:8081). Change the Airflow password before exposing the UI beyond your machine.

## Run the pipeline

In Airflow, unpause `changi_arrivals_daily` to enable its daily schedule: **06:00 UTC**, processing the UTC date two days earlier. Your computer and Docker must be running then; missed schedules are not automatically backfilled.

To run a specific day, choose **Trigger DAG** and enter this under **Configuration JSON** (replace the date as needed):

```json
{"process_date":"2026-11-15"}
```

Use the `YYYY-MM-DD` format. A successful run replaces only that date's BigQuery partition. Failed or empty source responses do not erase existing data. Avoid running the same date concurrently.

## Verify

Check that the Airflow run completed successfully, then query BigQuery:

```sql
SELECT flight_date, COUNT(*) AS flights
FROM `PROJECT.DATASET.flight_arrivals`
GROUP BY flight_date
ORDER BY flight_date;
```

Run the local tests and validate Compose configuration with:

```sh
pip install -e '.[test]'
pytest -q
docker compose config --quiet
```

Flight times are based on OpenSky observations, not an official airport timetable; coverage and origin estimates may be incomplete. BigQuery usage may incur charges.

Stop the services with `docker compose stop`. Use `docker compose down` to remove containers; `docker compose down -v` also deletes Airflow's local metadata database. BigQuery data is unaffected.
