"""Spark job entry point and processing date selection."""

import argparse
import os
from datetime import date, timedelta

import requests
from google.cloud import bigquery
from pyspark.sql import SparkSession

from flight_insights.extract import fetch_arrivals
from flight_insights.load import publish_day
from flight_insights.transform import transform_arrivals


def process_date(run_type, scheduled_time, config):
    if run_type == "manual":
        try:
            return date.fromisoformat(config["process_date"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Manual runs require process_date in YYYY-MM-DD format") from exc
    if run_type != "scheduled" or scheduled_time is None:
        raise ValueError("Unsupported run type")
    return scheduled_time.date() - timedelta(days=2)


def run(day, spark, session, client, project, dataset):
    try:
        records = fetch_arrivals(day, session)
        df = transform_arrivals(spark, records, day)
        publish_day(df, day, project, dataset, client)
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    project, dataset = os.environ["GOOGLE_CLOUD_PROJECT"], os.environ["BIGQUERY_DATASET"]
    client = bigquery.Client(project=project)
    spark = SparkSession.builder.appName("flight-insights").getOrCreate()
    with requests.Session() as session:
        run(args.date, spark, session, client, project, dataset)


if __name__ == "__main__":
    main()
