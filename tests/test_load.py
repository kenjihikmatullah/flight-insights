from datetime import date
from unittest.mock import MagicMock

import pytest

from flight_insights.load import publish_day


def test_publish_uses_staging_and_atomic_merge():
    client = MagicMock()
    client.get_table.return_value.schema = []
    client.query.return_value.result.return_value = [{"total": 3, "invalid": 0}]
    df = MagicMock()
    publish_day(df, date(2026, 11, 15), "my-project", "flight_insights", client)
    assert client.query.call_count == 2
    sql = client.query.call_args_list[1].args[0]
    assert "MERGE" in sql and "T.flight_date = @day" in sql and "ON FALSE" in sql
    assert df.write.format.return_value.option.return_value.mode.return_value.save.called
    client.delete_table.assert_called_once()


def test_invalid_stage_never_publishes():
    client = MagicMock()
    client.get_table.return_value.schema = []
    client.query.return_value.result.return_value = [{"total": 0, "invalid": 0}]
    with pytest.raises(ValueError):
        publish_day(MagicMock(), date(2026, 11, 15), "my-project", "flight_insights", client)
    assert client.query.call_count == 1
    client.delete_table.assert_called_once()


def test_invalid_identifier_rejected():
    with pytest.raises(ValueError):
        publish_day(MagicMock(), date.today(), "project`bad", "dataset", MagicMock())


def test_failed_write_preserves_error_and_cleans_stage():
    client = MagicMock()
    client.get_table.return_value.schema = []
    client.delete_table.side_effect = RuntimeError("cleanup failed")
    df = MagicMock()
    df.write.format.return_value.option.return_value.mode.return_value.save.side_effect = RuntimeError("write failed")
    with pytest.raises(RuntimeError, match="write failed"):
        publish_day(df, date(2026, 11, 15), "my-project", "dataset", client)
    client.query.assert_not_called()
    client.delete_table.assert_called_once()
