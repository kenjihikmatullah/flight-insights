from datetime import date

import pytest

from flight_insights.extract import fetch_arrivals, utc_window


class Response:
    def __init__(self, status, data):
        self.status_code, self.data = status, data

    def json(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(200, {"access_token": "token"})

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_window_and_request(monkeypatch):
    monkeypatch.setenv("OPENSKY_CLIENT_ID", "id")
    monkeypatch.setenv("OPENSKY_CLIENT_SECRET", "secret")
    day = date(2026, 11, 15)
    assert utc_window(day) == (1794700800, 1794787200)
    session = Session(Response(200, [{"icao24": "abc"}]))
    assert fetch_arrivals(day, session) == [{"icao24": "abc"}]
    assert session.calls[1][1]["params"] == {"airport": "WSSS", "begin": 1794700800, "end": 1794787200}
    assert session.calls[1][1]["headers"] == {"Authorization": "Bearer token"}


@pytest.mark.parametrize("response", [Response(404, []), Response(429, []), Response(200, []), Response(200, {}), Response(200, ValueError())])
def test_bad_responses_fail_closed(monkeypatch, response):
    monkeypatch.setenv("OPENSKY_CLIENT_ID", "id")
    monkeypatch.setenv("OPENSKY_CLIENT_SECRET", "secret")
    with pytest.raises(RuntimeError):
        fetch_arrivals(date(2026, 11, 15), Session(response))
