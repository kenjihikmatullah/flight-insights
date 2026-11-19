-- Replace PROJECT and DATASET before running.
CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.flight_arrivals` (
  flight_date DATE,
  arrival_airport STRING,
  origin_airport STRING,
  icao24 STRING,
  callsign STRING,
  first_seen_utc TIMESTAMP,
  last_seen_utc TIMESTAMP,
  observed_duration_minutes FLOAT64,
  ingested_at TIMESTAMP
)
PARTITION BY flight_date;
