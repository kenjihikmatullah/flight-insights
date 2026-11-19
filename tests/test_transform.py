from datetime import date

import pytest
from pyspark.sql import SparkSession

from flight_insights.transform import transform_arrivals


@pytest.fixture(scope="module")
def spark():
    session = SparkSession.builder.master("local[1]").appName("test").getOrCreate()
    yield session
    session.stop()


def test_transform_filters_and_deduplicates(spark):
    base = {"icao24": " ABC ", "firstSeen": 1794700800, "lastSeen": 1794704400, "estDepartureAirport": None, "callsign": " AB1 "}
    rows = [base, base.copy(), {**base, "icao24": ""}, {**base, "icao24": "xyz", "lastSeen": 1794787200}, {**base, "icao24": "bad", "firstSeen": 1794705000}]
    result = transform_arrivals(spark, rows, date(2026, 11, 15)).collect()
    assert len(result) == 1
    row = result[0]
    assert (row.icao24, row.callsign, row.origin_airport, row.observed_duration_minutes) == ("abc", "AB1", None, 60.0)
    assert row.flight_date == date(2026, 11, 15)


def test_empty_clean_batch_fails(spark):
    with pytest.raises(ValueError):
        transform_arrivals(spark, [{"icao24": ""}], date(2026, 11, 15))
