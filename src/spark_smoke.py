from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("flight-insights-smoke").getOrCreate()
try:
    assert spark.range(100, numPartitions=2).count() == 100
    print("Standalone Spark smoke test passed")
finally:
    spark.stop()
