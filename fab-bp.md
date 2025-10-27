# Microsoft Fabric Spark Best Practices Guide
## Comprehensive Guide for Data Engineering Excellence (2025)

**Document Version:** 1.0  
**Last Updated:** October 25, 2025  
**Runtime Version:** Fabric Runtime 1.3 (Apache Spark 3.5, Delta Lake 3.2)

---

## Table of Contents
1. [Introduction](#introduction)
2. [Runtime and Architecture](#runtime-and-architecture)
3. [Capacity Planning and Management](#capacity-planning-and-management)
4. [Spark Basics and Core Concepts](#spark-basics-and-core-concepts)
5. [Development Best Practices](#development-best-practices)
6. [Performance Optimization](#performance-optimization)
7. [Security Best Practices](#security-best-practices)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Cost Optimization](#cost-optimization)
10. [Code Examples](#code-examples)

---

## 1. Introduction

Microsoft Fabric provides a fully managed Apache Spark platform designed for enterprise-scale data engineering and data science workloads. This guide outlines best practices for optimizing performance, security, and cost when running Spark Notebooks and Spark Job Definitions (SJDs) on Microsoft Fabric.

### Key Features (2025)
- **Native Execution Engine (NEE)**: Up to 4x faster query performance
- **Starter Pools**: 5-10 second session initialization
- **Runtime 1.3**: Apache Spark 3.5 with Delta Lake 3.2
- **Autoscale Billing**: Serverless, pay-as-you-go model for Spark workloads
- **Autotune**: Automated performance optimization
- **Advanced Security**: OneLake Security with row/column-level access

---

## 2. Runtime and Architecture

### Current Runtime: Fabric Runtime 1.3

**Components:**
- **Apache Spark:** 3.5.2
- **Operating System:** Mariner 2.0
- **Java:** 11
- **Scala:** 2.12.18
- **Python:** 3.11
- **Delta Lake:** 3.2.1
- **R:** 4.3.3

### Native Execution Engine (NEE)
The Native Execution Engine, built on Meta's Velox and Intel's Apache Gluten, provides:
- Up to 4x faster query speeds compared to OSS Spark (TPC-DS 1TB benchmark)
- Supports both Parquet and Delta formats
- No code changes required
- Reduces operational costs across ETL, analytics, and interactive queries

### Compute Architecture

#### Starter Pools vs Custom Pools

**Starter Pools (Recommended for Most Workloads):**
```python
# Starter pools provide:
# - 5-10 second session initialization
# - Pre-warmed clusters
# - No manual configuration required
# - Automatic scaling
```

**When to Use Custom Pools:**
- Custom library dependencies (adds 30 seconds to 5 minutes startup time)
- Specific Spark configurations
- Advanced networking requirements (Private Links, Managed VNets)

**Important:** Starter Pools are NOT supported with Private Links or Managed VNets; in these cases, cluster creation takes 2-5 minutes.

---

## 3. Capacity Planning and Management

### Understanding Capacity Units (CUs)

**CU to vCore Conversion:**
- Every 1 CU = 2 Spark vCores
- Example: F128 capacity = 256 Spark vCores

### Capacity SKU Guidelines

| SKU | CUs | Spark vCores | Recommended Use Case |
|-----|-----|--------------|----------------------|
| F2  | 2   | 4            | Development/Testing |
| F4  | 4   | 8            | Small workloads |
| F8  | 8   | 16           | Small to medium workloads |
| F16 | 16  | 32           | Medium workloads |
| F32 | 32  | 64           | Production workloads |
| F64 | 64  | 128          | Large production (AI features available) |
| F128| 128 | 256          | Enterprise workloads |

**Note:** F64 or higher is required for AI Skills and Copilot features.

### Bursting and Smoothing

**Bursting:**
- Allows temporary overuse up to 3x base CU allocation
- Helps with concurrent workloads and peak demands
- Can be disabled by capacity admins via "Disable Job-level Bursting" switch

**Smoothing:**
- Spreads Spark operations over 24-hour period
- All Spark operations are background operations
- Reduces likelihood of throttling

### Autoscale Billing (NEW in 2025)

Serverless, pay-as-you-go model for Spark workloads:

**Benefits:**
- Dedicated Spark compute (no contention with other Fabric workloads)
- Pay only for execution time (0.5 CU Hour per job)
- Independent scaling from Fabric capacity
- Quota-aware controls via Azure Quota Management

**Configuration:**
```python
# Enable in Fabric Capacity Settings page
# Set maximum CU limit for budget control
# Jobs queue when limit reached (batch jobs)
# Jobs throttle when limit reached (interactive jobs)
```

### Monitoring Capacity Usage

```python
# Key metrics to monitor:
# 1. CU utilization trends
# 2. Throttling/rejection events
# 3. Active Spark sessions
# 4. Top consuming workspaces/items

# Use Fabric Capacity Metrics App for visualization
# Monitor via Admin monitoring workspace
# Track in Monitoring hub
```

---

## 4. Spark Basics and Core Concepts

### Executor Memory Model

Even with large executor memory (e.g., 56 GB), Spark doesn't allow all memory for user data:

```
┌─────────────────────────────────────┐
│ Reserved Memory (System/JVM)        │
├─────────────────────────────────────┤
│ User Memory (UDFs, variables)       │
├─────────────────────────────────────┤
│ Storage Memory (cached data)        │ ← Dynamic boundary
├─────────────────────────────────────┤
│ Execution Memory (shuffles, joins)  │
└─────────────────────────────────────┘
```

**Key Insight:** Storage and Execution memory boundaries are movable, allowing Spark to borrow between regions for optimal performance.

### Partitioning Best Practices

**Optimal Partition Size:**
- Target: 128 MB to 1 GB per partition
- Avoid: Very small (<10 MB) or very large (>2 GB) partitions

```python
# Check current partitions
df.rdd.getNumPartitions()

# Repartition for better parallelism
df = df.repartition(200)

# Coalesce to reduce partitions (no shuffle)
df = df.coalesce(50)
```

### Data Skew Detection and Resolution

**Symptoms:**
- Few tasks take much longer than others
- Large gap between median and max task times
- Uneven shuffle read/write sizes

**Solutions:**

```python
# 1. Key Salting
from pyspark.sql.functions import col, concat, lit, monotonically_increasing_id

# Add salt to skewed keys
df_salted = df.withColumn("salted_key", concat(col("key"), lit("_"), (monotonically_increasing_id() % 10)))

# 2. Adaptive Query Execution (AQE)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

# 3. Broadcast Join for small tables
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")
```

---

## 5. Development Best Practices

### Use DataFrame APIs (NOT RDDs)

**ALWAYS prefer DataFrame APIs** - the Catalyst optimizer optimizes built-in functions and runs them natively on the JVM.

```python
# ✅ GOOD: DataFrame API
df.filter(col("age") > 18).select("name", "age").show()

# ❌ BAD: RDD operations
df.rdd.filter(lambda x: x.age > 18).map(lambda x: (x.name, x.age)).collect()
```

### User Defined Functions (UDFs)

**Priority Order (Best to Worst):**

1. **Built-in Spark Functions** (BEST)
2. **Pandas UDFs** (Vectorized, use Apache Arrow)
3. **Scala/Java UDFs** (Run on JVM)
4. **Python UDFs** (AVOID - significant serialization overhead)

```python
# ✅ BEST: Built-in functions
from pyspark.sql.functions import upper, col
df = df.withColumn("name_upper", upper(col("name")))

# ✅ GOOD: Pandas UDF (when UDF needed)
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf("double")
def pandas_multiply(s: pd.Series) -> pd.Series:
    return s * 2

df = df.withColumn("doubled", pandas_multiply(col("value")))

# ❌ BAD: Regular Python UDF
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType

@udf(returnType=IntegerType())
def python_multiply(x):
    return x * 2  # Serialization overhead per row!

df = df.withColumn("doubled", python_multiply(col("value")))
```

### File Format Optimization

**Recommended Formats (in order):**

1. **Delta Lake** (BEST) - ACID transactions, time travel, Z-ordering
2. **Parquet** - Columnar, compressed, efficient
3. **ORC** - Optimized Row Columnar
4. **Avoid:** CSV, JSON for production workloads

```python
# ✅ BEST: Write as Delta with optimization
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("/path/to/delta/table")

# Optimize Delta table
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "/path/to/delta/table")
deltaTable.optimize().executeCompaction()

# Z-ORDER for common query patterns
deltaTable.optimize().executeZOrderBy("date", "customer_id")
```

### Environment Configuration

Use Fabric Environments to set default Spark properties:

```python
# Navigate to Workspace > New > Environment
# Set default Spark properties:

spark.sql.shuffle.partitions = 200
spark.sql.adaptive.enabled = true
spark.sql.adaptive.coalescePartitions.enabled = true
spark.databricks.delta.optimizeWrite.enabled = true
spark.databricks.delta.autoCompact.enabled = true
```

---

## 6. Performance Optimization

### Enable Adaptive Query Execution (AQE)

```python
# Enable AQE features
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")

# Set optimal partition sizes
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "134217728")  # 128 MB
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "1048576")  # 1 MB
```

### Caching Strategies

```python
# Cache when data is reused multiple times
df_cached = df.cache()

# Or persist with storage level
from pyspark.storagelevel import StorageLevel
df_persisted = df.persist(StorageLevel.MEMORY_AND_DISK)

# IMPORTANT: Unpersist when done
df_cached.unpersist()

# Check what's cached
spark.catalog.clearCache()
```

### Broadcast Joins

```python
from pyspark.sql.functions import broadcast

# Automatically broadcast small tables (<10MB default)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # 10 MB

# Explicitly broadcast small lookup tables
result = large_df.join(broadcast(small_lookup_df), "key")
```

### Delta Lake Optimizations

```python
from delta.tables import DeltaTable

# Enable automatic optimize write
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")

# Vacuum old files (keep 7 days)
deltaTable = DeltaTable.forPath(spark, "/path/to/delta")
deltaTable.vacuum(168)  # hours

# Z-ORDER for query performance
deltaTable.optimize().executeZOrderBy("date", "region")

# Enable column statistics
spark.conf.set("spark.databricks.delta.properties.defaults.collectStats", "true")
```

### Autotune (NEW in 2025)

Fabric Spark Autotune automatically optimizes Spark configurations:

```python
# Autotune recommendations available in Run Series Analysis
# Navigate to: Monitor > Apache Spark applications > Run Series
# Review Autotune suggestions for:
# - Shuffle partitions
# - Memory allocation
# - Executor configurations
```

---

## 7. Security Best Practices

### OneLake Security (GA in 2025)

Unified row and column-level security across Spark, SQL Endpoints, and Power BI:

```python
# OneLake Security enforces access policies automatically
# Policies defined in OneLake Security UI are respected by Spark

# Example: Reading data with OneLake security enabled
df = spark.read.format("delta").load("Tables/secured_table")
# User only sees rows/columns they have permission for

# No additional code required - security is transparent!
```

**Key Features:**
- Row-level security
- Column-level security
- Unified across all Fabric engines
- Automatic enforcement in Spark notebooks

### Workspace Outbound Access Protection (OAP)

Prevents data exfiltration by restricting outbound connectivity:

```python
# Enable OAP in Workspace Settings
# Configure Managed Private Endpoints for allowed destinations
# All other outbound connections are blocked

# OAP enforced automatically - no code changes needed
```

**Benefits:**
- Prevents unauthorized data export
- Controls which external destinations can be accessed
- Uses Managed Private Endpoints for approved connections
- Admin approval required for new endpoints

### Managed Virtual Networks

```python
# Managed VNets provide network isolation for Spark workloads
# Enable in workspace settings
# Clusters deployed in dedicated network (not shared)

# Connect to on-premises data via Managed Private Endpoints
# Support for Azure SQL Database, Azure Storage, etc.
```

### Secure Credential Management

```python
# ✅ GOOD: Use Azure Key Vault
from notebookutils import mssparkutils

# Get secret from Key Vault
secret_value = mssparkutils.credentials.getSecret("keyvault-name", "secret-name")

# Use in connection
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:sqlserver://server.database.windows.net:1433") \
    .option("dbtable", "schema.table") \
    .option("password", secret_value) \
    .load()

# ❌ BAD: Hardcoded credentials
password = "MyPassword123!"  # NEVER DO THIS
```

### Service Principal Authentication

```python
# Use Service Principals for automated jobs
# Configure in Fabric Settings > Workspace Identity

# Service Principals enable:
# - CI/CD automation
# - Secure, non-user authentication
# - Cross-tenant integration with Azure DevOps
```

---

## 8. Monitoring and Observability

### Logging Best Practices

```python
# ✅ BEST: Use Log4j for production
import traceback

# Get log4j logger
log4jLogger = spark._jvm.org.apache.log4j
logger = log4jLogger.LogManager.getLogger("MySparkApp")

logger.info("Application started")

try:
    # Your Spark operations
    data = [(f"Name{i}", i) for i in range(1, 21)]
    df = spark.createDataFrame(data, ["name", "age"])
    logger.info("DataFrame created successfully with 20 records")
    
    df.show()
    
except Exception as e:
    logger.error(f"Error occurred: {str(e)}\n{traceback.format_exc()}")
    # Application continues even after error

logger.info("Application completed")
```

### Azure Log Analytics Integration

```python
# Enable diagnostic emitter in Environment settings
# Configure in Environment > Spark compute > Diagnostic settings

# Send logs to Azure Log Analytics
spark.conf.set("spark.synapse.diagnostic.emitter.enabled", "true")
spark.conf.set("spark.synapse.diagnostic.emitter.azureLogAnalytics.enabled", "true")
spark.conf.set("spark.synapse.diagnostic.emitter.azureLogAnalytics.workspaceId", "workspace-id")
spark.conf.set("spark.synapse.diagnostic.emitter.azureLogAnalytics.secret", "secret-key")

# Filter specific loggers
spark.conf.set("spark.synapse.diagnostic.emitter.azureLogAnalytics.filter.loggerName.match", "MySparkApp")
```

### Monitoring APIs (GA in 2025)

```python
# Use Spark Monitoring APIs for programmatic access
# List Spark applications
# GET /v1/workspaces/{workspaceId}/sparkApplications

# Get application details
# GET /v1/workspaces/{workspaceId}/sparkApplications/{livyId}

# Spark Advisor API - performance recommendations
# GET /v1/workspaces/{workspaceId}/sparkApplications/{livyId}/advisor

# Resource Usage API - vCore allocation and utilization
# GET /v1/workspaces/{workspaceId}/sparkApplications/{livyId}/resources
```

### Run Series Analysis

```python
# Navigate to: Monitor > Apache Spark applications > Run Series
# Features:
# - Compare execution duration across recurring runs
# - Detect outliers and anomalies
# - Review Autotune recommendations
# - Analyze input/output data changes
# - Available even for running applications
```

### Monitor Spark Sessions

```python
# Check active sessions in notebook
spark.sparkContext.getConf().getAll()

# Stop session when done to save CU
# Toolbar: Stop session button

# Set session timeout (default 20 minutes)
# Workspace Settings > Data Engineering/Science > Spark compute
# Configure session timeout: 10-60 minutes
```

---

## 9. Cost Optimization

### Best Practices for CU Management

```python
# 1. ALWAYS stop interactive Spark sessions when done
# - Default timeout: 20 minutes
# - Sessions consume CU even when idle
# - Manually stop via notebook toolbar

# 2. Use appropriate cluster sizes
# Small (S) - 50% of Medium capacity
# Medium (M) - Default, balanced
# Large (L) - 2x Medium capacity

# 3. Configure in Workspace Settings > Spark compute
from notebookutils import mssparkutils

# Check current executor configuration
mssparkutils.runtime.context
```

### High Concurrency Mode

```python
# Share Spark session across multiple notebooks (same user)
# Enable via notebook toolbar: "New high concurrency session"

# Benefits:
# - Reduces CU consumption (avoid redundant session creation)
# - Faster execution (attach to running session)
# - Up to 5 notebooks per session

# Limitations:
# - User-specific (can't share across users)
# - Must use same default Lakehouse
# - Not suitable for scheduled workloads
```

### Optimize Write Operations

```python
# Enable optimize write and auto-compact for Delta
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")

# Set optimal file sizes
spark.conf.set("spark.sql.files.maxRecordsPerFile", "1000000")
spark.conf.set("spark.databricks.delta.targetFileSize", "134217728")  # 128 MB

# Reduce shuffle partitions for small datasets
spark.conf.set("spark.sql.shuffle.partitions", "50")  # Instead of default 200
```

### NotebookUtils RunMultiple

```python
from notebookutils import mssparkutils

# Execute multiple notebooks efficiently
# Structured as Directed Acyclic Graph (DAG)

# Parallel execution without extra compute
mssparkutils.notebook.runMultiple(
    {
        "nb1": {"path": "/notebook1"},
        "nb2": {"path": "/notebook2"},
        "nb3": {"path": "/notebook3", "dependencies": ["nb1", "nb2"]}
    }
)
```

### Autoscale Billing Consideration

```python
# Use Autoscale Billing for sporadic Spark workloads
# Enable in Capacity Settings > Autoscale Billing

# Benefits:
# - Pay only for execution time (0.5 CU Hour)
# - No idle compute costs
# - Independent from Fabric capacity
# - Set max CU limit for budget control

# When NOT to use:
# - Continuous, high-volume workloads
# - When capacity bursting is sufficient
```

---

## 10. Code Examples

### Example 1: Efficient ETL Pipeline

```python
from pyspark.sql.functions import col, current_timestamp, lit, when
from delta.tables import DeltaTable

# Initialize log4j logger
log4jLogger = spark._jvm.org.apache.log4j
logger = log4jLogger.LogManager.getLogger("ETLPipeline")

logger.info("Starting ETL pipeline")

# Enable optimizations
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")

# Read source data
source_df = spark.read \
    .format("parquet") \
    .load("Files/raw/sales/*.parquet")

logger.info(f"Loaded {source_df.count()} records from source")

# Transform data
transformed_df = source_df \
    .filter(col("amount") > 0) \
    .withColumn("processed_timestamp", current_timestamp()) \
    .withColumn("year", col("order_date").substr(1, 4)) \
    .withColumn("month", col("order_date").substr(6, 2)) \
    .withColumn("revenue_category", 
                when(col("amount") < 100, "low")
                .when(col("amount") < 1000, "medium")
                .otherwise("high"))

# Write to Delta table with partitioning
output_path = "Tables/processed_sales"

transformed_df.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("year", "month") \
    .option("overwriteSchema", "true") \
    .save(output_path)

logger.info("Data written to Delta table")

# Optimize Delta table
deltaTable = DeltaTable.forPath(spark, output_path)
deltaTable.optimize().executeCompaction()
deltaTable.optimize().executeZOrderBy("customer_id", "order_date")

logger.info("ETL pipeline completed successfully")
```

### Example 2: Incremental Data Processing

```python
from delta.tables import DeltaTable
from pyspark.sql.functions import col, max

logger = log4jLogger.LogManager.getLogger("IncrementalLoad")

# Read checkpoint for last processed timestamp
checkpoint_path = "Tables/checkpoints/sales_checkpoint"

try:
    checkpoint_df = spark.read.format("delta").load(checkpoint_path)
    last_processed = checkpoint_df.select(max("max_timestamp")).collect()[0][0]
    logger.info(f"Last processed timestamp: {last_processed}")
except:
    last_processed = "2020-01-01 00:00:00"
    logger.info("No checkpoint found, starting from beginning")

# Read only new records
source_df = spark.read \
    .format("delta") \
    .load("Tables/raw_events") \
    .filter(col("event_timestamp") > last_processed)

new_records = source_df.count()
logger.info(f"Processing {new_records} new records")

if new_records > 0:
    # Transform new records
    processed_df = source_df.select(
        col("event_id"),
        col("user_id"),
        col("event_type"),
        col("event_timestamp"),
        col("event_data")
    )
    
    # Append to target table
    deltaTable = DeltaTable.forPath(spark, "Tables/processed_events")
    
    deltaTable.alias("target").merge(
        processed_df.alias("source"),
        "target.event_id = source.event_id"
    ).whenNotMatchedInsertAll().execute()
    
    # Update checkpoint
    new_checkpoint = source_df.select(max("event_timestamp").alias("max_timestamp"))
    new_checkpoint.write.format("delta").mode("overwrite").save(checkpoint_path)
    
    logger.info("Incremental load completed successfully")
else:
    logger.info("No new records to process")
```

### Example 3: Data Quality Checks

```python
from pyspark.sql.functions import col, count, when, isnan, isnull

logger = log4jLogger.LogManager.getLogger("DataQuality")

# Read data
df = spark.read.format("delta").load("Tables/customer_data")

logger.info("Starting data quality checks")

# Quality metrics
total_records = df.count()

# Check for nulls in critical columns
critical_columns = ["customer_id", "email", "registration_date"]
null_checks = []

for column in critical_columns:
    null_count = df.filter(col(column).isNull()).count()
    null_percentage = (null_count / total_records) * 100
    
    null_checks.append({
        "column": column,
        "null_count": null_count,
        "null_percentage": round(null_percentage, 2)
    })
    
    logger.info(f"{column}: {null_count} nulls ({null_percentage:.2f}%)")

# Check for duplicates
duplicate_count = df.groupBy("customer_id").count().filter(col("count") > 1).count()
logger.info(f"Duplicate customer_ids: {duplicate_count}")

# Check data ranges
date_issues = df.filter(
    (col("registration_date") < "2010-01-01") | 
    (col("registration_date") > current_timestamp())
).count()
logger.info(f"Invalid registration dates: {date_issues}")

# Create quality report
quality_report = spark.createDataFrame([
    ("total_records", total_records),
    ("duplicate_customer_ids", duplicate_count),
    ("invalid_dates", date_issues)
], ["metric", "value"])

# Save quality report
quality_report.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .save("Tables/data_quality_reports")

# Raise alert if quality issues detected
if duplicate_count > 0 or date_issues > 0:
    logger.warn(f"Data quality issues detected!")
else:
    logger.info("All data quality checks passed")
```

### Example 4: Optimized Join Operations

```python
from pyspark.sql.functions import broadcast, col

logger = log4jLogger.LogManager.getLogger("JoinOptimization")

# Read tables
customers = spark.read.format("delta").load("Tables/customers")
orders = spark.read.format("delta").load("Tables/orders")
products = spark.read.format("delta").load("Tables/products")

logger.info("Starting join operations")

# Enable AQE for skew join handling
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# Broadcast small dimension tables
result = orders \
    .join(broadcast(customers), "customer_id") \
    .join(broadcast(products), "product_id") \
    .select(
        col("order_id"),
        col("order_date"),
        col("customer_name"),
        col("product_name"),
        col("quantity"),
        col("unit_price"),
        (col("quantity") * col("unit_price")).alias("total_amount")
    )

# Repartition by a commonly used column for downstream processing
result = result.repartition(50, "order_date")

# Write partitioned result
result.write \
    .format("delta") \
    .mode("overwrite") \
    .partitionBy("order_date") \
    .save("Tables/order_details")

logger.info("Join operations completed successfully")
```

### Example 5: Working with Large Files

```python
from pyspark.sql.functions import col, input_file_name

logger = log4jLogger.LogManager.getLogger("LargeFileProcessing")

# Read large CSV files with proper partitioning
large_df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .option("mode", "DROPMALFORMED") \
    .csv("Files/large_dataset/*.csv")

logger.info(f"Loaded data with {large_df.rdd.getNumPartitions()} partitions")

# Repartition for better parallelism (aim for 128MB-1GB per partition)
target_partitions = 200
large_df = large_df.repartition(target_partitions)

# Process in batches if very large
batch_size = 1000000
total_records = large_df.count()
num_batches = (total_records // batch_size) + 1

logger.info(f"Processing {total_records} records in {num_batches} batches")

# Write optimized Delta table
large_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("dataChange", "false") \
    .option("maxRecordsPerFile", 1000000) \
    .save("Tables/optimized_large_dataset")

# Compact small files
deltaTable = DeltaTable.forPath(spark, "Tables/optimized_large_dataset")
deltaTable.optimize().executeCompaction()

logger.info("Large file processing completed")
```

### Example 6: Monitoring Resource Usage

```python
# Real-time monitoring in notebook
from notebookutils import mssparkutils
import json

# Get current Spark context info
context_info = mssparkutils.runtime.context

print("=== Spark Session Configuration ===")
print(f"Workspace Name: {context_info['workspaceName']}")
print(f"Pool Name: {context_info['poolName']}")
print(f"Cluster Size: {context_info['nodeSize']}")

# Get Spark configuration
spark_config = spark.sparkContext.getConf().getAll()
print("\n=== Key Spark Configurations ===")
for key, value in spark_config:
    if any(x in key for x in ['executor', 'driver', 'memory', 'cores']):
        print(f"{key}: {value}")

# Monitor partition distribution
def check_partition_distribution(df, table_name):
    partitions = df.rdd.getNumPartitions()
    record_count = df.count()
    records_per_partition = record_count / partitions
    
    print(f"\n=== {table_name} Partition Stats ===")
    print(f"Total Partitions: {partitions}")
    print(f"Total Records: {record_count}")
    print(f"Avg Records/Partition: {records_per_partition:.0f}")
    
    if records_per_partition < 10000:
        print("⚠️ Warning: Too many small partitions. Consider coalesce()")
    elif records_per_partition > 10000000:
        print("⚠️ Warning: Partitions too large. Consider repartition()")
    else:
        print("✓ Partition size looks good")

# Example usage
df = spark.read.format("delta").load("Tables/sales")
check_partition_distribution(df, "Sales Table")
```

---

## Summary: Top 10 Quick Wins

1. **Use Runtime 1.3** - Latest features and 4x performance improvements with NEE
2. **Enable AQE** - Automatic query optimization and skew handling
3. **Use DataFrame APIs** - Never use RDDs; avoid Python UDFs
4. **Optimize Delta Tables** - Enable optimize write, auto-compact, and Z-ordering
5. **Stop Sessions** - Manually stop interactive sessions to save CU
6. **Use Broadcast Joins** - For small lookup tables (<10 MB)
7. **Right-size Partitions** - Target 128 MB to 1 GB per partition
8. **Log4j for Production** - Proper logging for monitoring and debugging
9. **OneLake Security** - Leverage unified security across all engines
10. **Monitor with APIs** - Use Spark Monitoring APIs and Run Series Analysis

---

## Additional Resources

### Official Documentation
- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Spark Best Practices Overview](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-best-practices-overview)
- [Spark Monitoring APIs](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-monitoring-api-overview)

### Tools
- **Fabric Capacity Metrics App** - Monitor CU consumption
- **Fabric SKU Estimator** - Plan capacity requirements
- **Run Series Analysis** - Optimize recurring Spark jobs
- **Monitoring Hub** - Track active Spark sessions

### Support
- [Microsoft Fabric Blog](https://blog.fabric.microsoft.com/)
- [Microsoft Fabric Community](https://community.fabric.microsoft.com/)
- [Support Portal](https://support.microsoft.com/fabric)

---

**Document prepared by:** Microsoft Fabric Platform Expert  
**Based on:** Official Microsoft documentation and best practices as of October 2025  
**Runtime Version:** Fabric Runtime 1.3 (Apache Spark 3.5, Delta Lake 3.2)

*Note: This document reflects the current state of Microsoft Fabric as of October 2025. Features and best practices may evolve. Always refer to official Microsoft documentation for the latest updates.*
