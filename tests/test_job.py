from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from flight_insights.job import process_date, run


def test_scheduled_and_manual_dates():
    assert process_date("scheduled", datetime(2026, 11, 17, 6, tzinfo=timezone.utc), {}) == date(2026, 11, 15)
    assert process_date("manual", None, {"process_date": "2026-11-10"}) == date(2026, 11, 10)
    with pytest.raises(ValueError):
        process_date("manual", None, {})


def test_job_stops_spark_on_failure(monkeypatch):
    spark = MagicMock()
    monkeypatch.setattr("flight_insights.job.fetch_arrivals", MagicMock(side_effect=RuntimeError("bad source")))
    with pytest.raises(RuntimeError):
        run(date(2026, 11, 15), spark, MagicMock(), MagicMock(), "my-project", "data")
    spark.stop.assert_called_once()
