"""Retrieve observed arrivals from OpenSky."""

import os
from datetime import datetime, time, timedelta, timezone

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
ARRIVALS_URL = "https://opensky-network.org/api/flights/arrival"


def utc_window(day):
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    return int(start.timestamp()), int((start + timedelta(days=1)).timestamp())


def _json(response, label):
    if response.status_code != 200:
        raise RuntimeError(f"{label} returned HTTP {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"{label} returned invalid JSON") from exc


def fetch_arrivals(day, session):
    client_id = os.environ["OPENSKY_CLIENT_ID"]
    secret = os.environ["OPENSKY_CLIENT_SECRET"]
    token_data = _json(session.post(TOKEN_URL, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret}, timeout=15), "OpenSky authentication")
    token = token_data.get("access_token") if isinstance(token_data, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError("OpenSky authentication returned no access token")
    begin, end = utc_window(day)
    response = session.get(ARRIVALS_URL, params={"airport": "WSSS", "begin": begin, "end": end}, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    records = _json(response, "OpenSky arrivals")
    if not isinstance(records, list) or not records or not all(isinstance(row, dict) for row in records):
        raise RuntimeError("OpenSky arrivals returned no usable records")
    return records
