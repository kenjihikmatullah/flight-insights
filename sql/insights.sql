-- Replace PROJECT.DATASET and the sample UTC dates before running.
-- Arrival hours are Singapore local time, grouped within each UTC date.
SELECT flight_date, EXTRACT(HOUR FROM DATETIME(last_seen_utc, 'Asia/Singapore')) AS singapore_hour,
       COUNT(*) AS observed_arrivals
FROM `PROJECT.DATASET.flight_arrivals`
WHERE flight_date BETWEEN DATE '2026-11-01' AND DATE '2026-11-30'
GROUP BY 1, 2 ORDER BY 1, observed_arrivals DESC;

SELECT COALESCE(origin_airport, 'UNKNOWN') AS estimated_origin, COUNT(*) AS observed_arrivals
FROM `PROJECT.DATASET.flight_arrivals`
WHERE flight_date BETWEEN DATE '2026-11-01' AND DATE '2026-11-30'
GROUP BY 1 ORDER BY 2 DESC;

SELECT flight_date, COUNT(*) AS observed_arrivals
FROM `PROJECT.DATASET.flight_arrivals`
WHERE flight_date BETWEEN DATE '2026-11-01' AND DATE '2026-11-30'
GROUP BY 1 ORDER BY 1;
