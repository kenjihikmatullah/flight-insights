"""Publish one day using a BigQuery staging table and atomic MERGE."""

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from google.cloud import bigquery

LOG = logging.getLogger(__name__)
FIELDS = ("flight_date", "arrival_airport", "origin_airport", "icao24", "callsign", "first_seen_utc", "last_seen_utc", "observed_duration_minutes", "ingested_at")


def publish_day(df, day, project, dataset, bq_client):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,1023}", dataset):
        raise ValueError("Invalid BigQuery project or dataset identifier")
    target = f"{project}.{dataset}.flight_arrivals"
    stage = f"{project}.{dataset}.stage_arrivals_{uuid.uuid4().hex}"
    table = bigquery.Table(stage, schema=bq_client.get_table(target).schema)
    table.expires = datetime.now(timezone.utc) + timedelta(hours=24)
    bq_client.create_table(table)
    parameters = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("day", "DATE", day)])
    try:
        df.write.format("bigquery").option("writeMethod", "direct").mode("append").save(stage)
        result = bq_client.query(f"SELECT COUNT(*) AS total, COUNTIF(flight_date IS NULL OR flight_date != @day) AS invalid FROM `{stage}`", job_config=parameters).result()
        counts = next(iter(result))
        if counts["total"] == 0 or counts["invalid"]:
            raise ValueError("Staging table is empty or contains an unexpected date")
        columns = ", ".join(FIELDS)
        values = ", ".join(f"S.{field}" for field in FIELDS)
        sql = f"""MERGE `{target}` AS T
USING (SELECT * FROM `{stage}` WHERE flight_date = @day) AS S ON FALSE
WHEN NOT MATCHED BY SOURCE AND T.flight_date = @day THEN DELETE
WHEN NOT MATCHED BY TARGET THEN INSERT ({columns}) VALUES ({values})"""
        bq_client.query(sql, job_config=parameters).result()
    finally:
        try:
            bq_client.delete_table(stage, not_found_ok=True)
        except Exception:
            LOG.exception("Failed to delete staging table %s; it expires automatically", stage)
