"""Convert OpenSky observations into the BigQuery data contract."""

from pyspark.sql import Window, functions as F, types as T

from flight_insights.extract import utc_window

INPUT_SCHEMA = T.StructType([
    T.StructField("icao24", T.StringType()),
    T.StructField("callsign", T.StringType()),
    T.StructField("estDepartureAirport", T.StringType()),
    T.StructField("firstSeen", T.LongType()),
    T.StructField("lastSeen", T.LongType()),
])


def transform_arrivals(spark, records, day):
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    # Restrict to known fields so unexpected source additions do not affect schema.
    data = [{field.name: row.get(field.name) for field in INPUT_SCHEMA} for row in records]
    df = spark.createDataFrame(data, INPUT_SCHEMA)
    begin, end = utc_window(day)
    df = df.withColumn("icao24", F.lower(F.trim("icao24")))
    for col in ("callsign", "estDepartureAirport"):
        df = df.withColumn(col, F.when(F.length(F.trim(F.col(col))) > 0, F.trim(F.col(col))))
    df = df.filter((F.length("icao24") > 0) & (F.col("firstSeen") > 0) & (F.col("firstSeen") <= F.col("lastSeen")) & (F.col("lastSeen") >= begin) & (F.col("lastSeen") < end))
    order = Window.partitionBy("icao24", "firstSeen", "lastSeen").orderBy(F.col("estDepartureAirport").asc_nulls_last(), F.col("callsign").asc_nulls_last())
    df = df.withColumn("rank", F.row_number().over(order)).filter(F.col("rank") == 1)
    df = df.select(F.to_date(F.col("lastSeen").cast("timestamp")).alias("flight_date"), F.lit("WSSS").alias("arrival_airport"), F.col("estDepartureAirport").alias("origin_airport"), "icao24", "callsign", F.col("firstSeen").cast("timestamp").alias("first_seen_utc"), F.col("lastSeen").cast("timestamp").alias("last_seen_utc"), ((F.col("lastSeen") - F.col("firstSeen")) / 60.0).alias("observed_duration_minutes"), F.current_timestamp().alias("ingested_at"))
    if not df.take(1):
        raise ValueError("No valid arrivals in source batch")
    return df
