# Delta Table Maintenance - Production Guide

## Overview

Production-ready notebook implementation for Delta table maintenance operations including OPTIMIZE, VACUUM, and ANALYZE. Designed for monthly scheduled execution in Microsoft Fabric.

---

## Notebook Code

```python
# METADATA ***********************************************************
# TITLE: Delta Table Maintenance - Production
# AUTHOR: Fabric Data Engineering
# SCHEDULE: Monthly (1st day of month, 2 AM UTC)
# DESCRIPTION: OPTIMIZE, VACUUM, and ANALYZE operations for Delta tables
# *********************************************************************

from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from datetime import datetime
import json

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    "lakehouse_path": lh_gold_path,  # Your resolved path
    "retention_hours": 168,  # 7 days (minimum allowed in Fabric)
    "target_file_size_mb": 128,  # OPTIMIZE target file size
    "max_concurrent_tasks": 4,  # Parallelism for operations
    "enable_vacuum": True,
    "enable_optimize": True,
    "enable_analyze": True,
    "z_order_columns": {  # Table-specific Z-ORDER columns
        # "table_name": ["col1", "col2"],
        # "sales_fact": ["date_key", "customer_key"]
    },
    "exclude_tables": [],  # Tables to skip
    "dry_run": False
}

# =============================================================================
# UTILITIES
# =============================================================================

class MaintenanceLogger:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def log(self, table_name, operation, status, duration_sec=None, details=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "table": table_name,
            "operation": operation,
            "status": status,
            "duration_sec": duration_sec,
            "details": details
        }
        self.results.append(entry)
        print(f"[{status}] {table_name} - {operation}: {details or ''}")
    
    def get_summary(self):
        total_duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_duration_sec": total_duration,
            "operations": len(self.results),
            "successful": sum(1 for r in self.results if r["status"] == "SUCCESS"),
            "failed": sum(1 for r in self.results if r["status"] == "FAILED"),
            "skipped": sum(1 for r in self.results if r["status"] == "SKIPPED"),
            "details": self.results
        }

logger = MaintenanceLogger()

# =============================================================================
# MAINTENANCE OPERATIONS
# =============================================================================

def get_delta_tables(lakehouse_path):
    """Discover all Delta tables in lakehouse"""
    try:
        tables = []
        # List all directories in lakehouse Tables folder
        table_paths = mssparkutils.fs.ls(f"{lakehouse_path}/Tables")
        
        for table_path in table_paths:
            if table_path.isDir:
                table_name = table_path.name.rstrip('/')
                full_path = f"{lakehouse_path}/Tables/{table_name}"
                
                # Verify it's a Delta table
                try:
                    DeltaTable.forPath(spark, full_path)
                    tables.append((table_name, full_path))
                except:
                    logger.log(table_name, "DISCOVERY", "SKIPPED", 
                             details="Not a Delta table")
        
        return tables
    except Exception as e:
        logger.log("DISCOVERY", "GET_TABLES", "FAILED", details=str(e))
        raise

def optimize_table(table_name, table_path, z_order_cols=None):
    """Run OPTIMIZE with optional Z-ORDER"""
    if CONFIG["dry_run"]:
        logger.log(table_name, "OPTIMIZE", "SKIPPED", details="Dry run mode")
        return
    
    try:
        start = datetime.now()
        delta_table = DeltaTable.forPath(spark, table_path)
        
        # Configure OPTIMIZE
        optimize_cmd = delta_table.optimize()
        
        if z_order_cols:
            optimize_cmd = optimize_cmd.executeZOrderBy(z_order_cols)
            operation = f"OPTIMIZE + Z-ORDER({', '.join(z_order_cols)})"
        else:
            optimize_cmd.executeCompaction()
            operation = "OPTIMIZE"
        
        duration = (datetime.now() - start).total_seconds()
        logger.log(table_name, operation, "SUCCESS", duration_sec=duration)
        
    except Exception as e:
        logger.log(table_name, "OPTIMIZE", "FAILED", details=str(e))

def vacuum_table(table_name, table_path, retention_hours):
    """Run VACUUM to remove old files"""
    if CONFIG["dry_run"]:
        logger.log(table_name, "VACUUM", "SKIPPED", details="Dry run mode")
        return
    
    try:
        start = datetime.now()
        delta_table = DeltaTable.forPath(spark, table_path)
        delta_table.vacuum(retention_hours)
        
        duration = (datetime.now() - start).total_seconds()
        logger.log(table_name, "VACUUM", "SUCCESS", duration_sec=duration,
                  details=f"{retention_hours}h retention")
        
    except Exception as e:
        logger.log(table_name, "VACUUM", "FAILED", details=str(e))

def analyze_table(table_name, table_path):
    """Update table statistics"""
    if CONFIG["dry_run"]:
        logger.log(table_name, "ANALYZE", "SKIPPED", details="Dry run mode")
        return
    
    try:
        start = datetime.now()
        spark.sql(f"ANALYZE TABLE delta.`{table_path}` COMPUTE STATISTICS FOR ALL COLUMNS")
        
        duration = (datetime.now() - start).total_seconds()
        logger.log(table_name, "ANALYZE", "SUCCESS", duration_sec=duration)
        
    except Exception as e:
        logger.log(table_name, "ANALYZE", "FAILED", details=str(e))

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_maintenance():
    """Execute maintenance workflow"""
    print("=" * 80)
    print(f"Delta Table Maintenance - Started: {datetime.now().isoformat()}")
    print(f"Lakehouse: {CONFIG['lakehouse_path']}")
    print(f"Dry Run: {CONFIG['dry_run']}")
    print("=" * 80)
    
    # Discover tables
    tables = get_delta_tables(CONFIG["lakehouse_path"])
    print(f"\nFound {len(tables)} Delta tables")
    
    # Process each table
    for table_name, table_path in tables:
        print(f"\n--- Processing: {table_name} ---")
        
        # Skip excluded tables
        if table_name in CONFIG["exclude_tables"]:
            logger.log(table_name, "ALL", "SKIPPED", details="In exclude list")
            continue
        
        # OPTIMIZE
        if CONFIG["enable_optimize"]:
            z_order_cols = CONFIG["z_order_columns"].get(table_name)
            optimize_table(table_name, table_path, z_order_cols)
        
        # VACUUM
        if CONFIG["enable_vacuum"]:
            vacuum_table(table_name, table_path, CONFIG["retention_hours"])
        
        # ANALYZE
        if CONFIG["enable_analyze"]:
            analyze_table(table_name, table_path)
    
    # Summary
    summary = logger.get_summary()
    print("\n" + "=" * 80)
    print("MAINTENANCE SUMMARY")
    print("=" * 80)
    print(f"Total Duration: {summary['total_duration_sec']:.2f}s")
    print(f"Operations: {summary['operations']}")
    print(f"  Success: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Skipped: {summary['skipped']}")
    
    # Write results to Delta table for tracking
    results_df = spark.createDataFrame([summary])
    results_df.write.format("delta").mode("append").save(
        f"{CONFIG['lakehouse_path']}/Tables/_maintenance_logs"
    )
    
    return summary

# Execute
summary = run_maintenance()
```

---

## Scheduling - Monthly Execution

### Method 1: Fabric Pipeline (Recommended)

**Setup Steps:**

1. **Create Pipeline**
   - Navigate to: Data Factory → New Pipeline
   - Name: `pipe_monthly_maintenance`
   - Add **Notebook** activity
   - Select your maintenance notebook
   - Configure lakehouse attachment

2. **Configure Schedule Trigger**
   ```
   Trigger Type: Schedule
   Frequency: Month
   Start Date: 2025-12-01 02:00:00 UTC
   Time Zone: UTC
   Recurrence: On day 1
   At: 02:00
   ```

3. **Set Retry Policy**
   - Retry Attempts: 2
   - Retry Interval: 30 seconds
   - Timeout: 4 hours (adjust based on table sizes)

4. **Enable Monitoring**
   - Pipeline Runs: Track execution history
   - Alert on Failure: Configure email notifications

### Method 2: Notebook Direct Scheduler

**Steps:**
- Open Notebook → **Run** → **Schedule**
- Frequency: Monthly
- Day of Month: 1
- Time: 02:00 UTC

**⚠️ Limitation**: Less robust than pipeline approach, limited retry logic

### Method 3: Data Activator (Event-Driven)

For trigger-based execution instead of time-based:

```sql
-- Create monitoring table
CREATE TABLE maintenance_trigger (
    execution_date DATE,
    should_run BOOLEAN
);

-- Use Data Activator to monitor and trigger pipeline when should_run = TRUE
```

---

## Critical Issues & Considerations

### 1. VACUUM Retention Minimum

**Issue**: Fabric enforces minimum 168 hours (7 days) retention
- Lower values will fail silently or error
- Time travel queries beyond retention window will fail
- Cannot set below 7 days even with `spark.databricks.delta.retentionDurationCheck.enabled = false`

**Recommendation**: Keep at 168 hours unless specific compliance requirements

### 2. OPTIMIZE File Size Configuration

Configure at session level for consistent file sizing:

```python
# Add to notebook startup cell
spark.conf.set("spark.databricks.delta.optimize.maxFileSize", 134217728)  # 128 MB
spark.conf.set("spark.databricks.delta.optimize.minFileSize", 67108864)   # 64 MB
```

**File Size Guidelines**:
- Small tables (<1GB): 64-128 MB
- Medium tables (1-100GB): 128-256 MB
- Large tables (>100GB): 256-512 MB

### 3. Z-ORDER Column Selection

**Best Practices**:
- Choose **high-cardinality** columns used in WHERE/JOIN clauses
- Maximum 4 columns (diminishing returns after)
- Order by filter frequency (most filtered first)

**Good Candidates**:
```python
"z_order_columns": {
    "sales_fact": ["date_key", "customer_key"],
    "customer_dim": ["customer_id", "state_code"],
    "transactions": ["transaction_date", "user_id"]
}
```

**Avoid Z-ORDER On**:
- Low-cardinality columns (status flags, boolean)
- Constantly changing columns
- Columns rarely used in queries

### 4. Concurrent Operations Risk

```python
# Set in CONFIG based on Fabric SKU
"max_concurrent_tasks": 4  # F32/F64
"max_concurrent_tasks": 2  # F8/F16
```

**Risk**: Exceeding capacity unit limits causes:
- Pipeline failures
- Query throttling
- Impact to concurrent users

### 5. Long-Running Tables

**Issue**: Partitioned tables (1B+ rows) can take 30+ minutes per operation

**Solutions**:

**Option A - Partition-Level Optimization**:
```python
def optimize_partitioned_table(table_path, partition_col):
    """Optimize by partition for large tables"""
    partitions = spark.sql(f"SHOW PARTITIONS delta.`{table_path}`").collect()
    
    for partition in partitions:
        partition_value = partition[0].split('=')[1]
        spark.sql(f"""
            OPTIMIZE delta.`{table_path}` 
            WHERE {partition_col} = '{partition_value}'
        """)
```

**Option B - Incremental Approach**:
```python
# Only optimize recent partitions monthly, full optimization quarterly
recent_partitions = spark.sql(f"""
    SELECT DISTINCT {partition_col}
    FROM delta.`{table_path}`
    WHERE {partition_col} >= CURRENT_DATE - INTERVAL 30 DAYS
""").collect()
```

### 6. Memory Pressure

**Issue**: ANALYZE ALL COLUMNS can OOM on wide tables (100+ columns)

**Solution**:
```python
def analyze_table_selective(table_name, table_path):
    """Analyze only frequently queried columns"""
    important_cols = ["date_key", "customer_key", "amount"]  # Define per table
    col_list = ", ".join(important_cols)
    
    spark.sql(f"""
        ANALYZE TABLE delta.`{table_path}` 
        COMPUTE STATISTICS FOR COLUMNS {col_list}
    """)
```

---

## Performance Expectations

### Duration by Table Size

| Operation | Small (<10GB) | Medium (10-100GB) | Large (>100GB) |
|-----------|---------------|-------------------|----------------|
| OPTIMIZE  | 30s - 2min    | 5-15min          | 20-60min       |
| VACUUM    | 10-30s        | 1-5min           | 5-20min        |
| ANALYZE   | 5-15s         | 30s-2min         | 2-10min        |

### Fabric SKU Impact

| SKU    | Recommendation |
|--------|----------------|
| F2/F4  | Run during off-hours only (2-4 AM) |
| F8-F32 | Can run during business hours with throttling |
| F64+   | Minimal user impact, can run anytime |

### Expected Improvements Post-Optimization

**Query Performance**:
- 30-70% reduction in query time (scan-heavy queries)
- 10-30% reduction (point lookups with Z-ORDER)

**Storage**:
- 20-40% reduction in storage costs (via VACUUM)
- Improved compression ratios

**Compute**:
- Lower CU consumption per query
- Fewer file operations

---

## Monitoring & Alerting

### Check Maintenance History

```sql
-- Query maintenance logs
SELECT 
    timestamp,
    table,
    operation,
    status,
    duration_sec,
    details
FROM gold._maintenance_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL 30 DAYS
ORDER BY timestamp DESC;
```

### Identify Problem Tables

```sql
-- Find tables with failed operations
SELECT 
    table,
    COUNT(*) as failure_count,
    MAX(timestamp) as last_failure,
    MAX(details) as last_error
FROM gold._maintenance_logs
WHERE status = 'FAILED'
    AND timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY table
ORDER BY failure_count DESC;
```

### Track Performance Trends

```sql
-- Monitor duration trends
SELECT 
    table,
    operation,
    AVG(duration_sec) as avg_duration,
    MAX(duration_sec) as max_duration,
    COUNT(*) as run_count
FROM gold._maintenance_logs
WHERE status = 'SUCCESS'
    AND timestamp >= CURRENT_DATE - INTERVAL 90 DAYS
GROUP BY table, operation
ORDER BY avg_duration DESC;
```

### Pipeline Monitoring Dashboard

Create a Power BI report connected to `_maintenance_logs`:
- KPI tiles: Success rate, avg duration, tables processed
- Line chart: Duration trends over time
- Table visual: Failed operations with error details
- Matrix: Operation status by table

---

## Troubleshooting

### Common Issues

**1. VACUUM fails with "retention period not met"**
```python
# Cause: Attempting VACUUM with < 168 hours
# Solution: Set retention_hours to 168 minimum
CONFIG["retention_hours"] = 168
```

**2. OPTIMIZE times out**
```python
# Cause: Table too large for single operation
# Solution: Implement partition-level optimization
optimize_partitioned_table(table_path, "date_partition")
```

**3. ANALYZE fails on specific columns**
```python
# Cause: Complex data types (arrays, structs) not supported
# Solution: Exclude problematic columns
spark.sql(f"""
    ANALYZE TABLE delta.`{table_path}` 
    COMPUTE STATISTICS FOR COLUMNS col1, col2
""")
```

**4. Out of Memory during maintenance**
```python
# Cause: Insufficient executor memory
# Solution: Reduce concurrent operations
CONFIG["max_concurrent_tasks"] = 1

# Or increase executor memory in notebook settings:
spark.conf.set("spark.executor.memory", "16g")
```

**5. Pipeline fails to start at scheduled time**
- Verify trigger is active (not paused)
- Check workspace capacity state
- Ensure notebook is not in edit mode
- Validate lakehouse is attached to notebook

---

## Advanced Configuration

### Selective Maintenance by Pattern

```python
def run_maintenance_selective():
    """Run different operations based on table patterns"""
    tables = get_delta_tables(CONFIG["lakehouse_path"])
    
    for table_name, table_path in tables:
        # Fact tables: Full maintenance
        if table_name.endswith("_fact"):
            optimize_table(table_name, table_path, z_order_cols=["date_key"])
            vacuum_table(table_name, table_path, 168)
            analyze_table(table_name, table_path)
        
        # Dimension tables: Optimize only
        elif table_name.endswith("_dim"):
            optimize_table(table_name, table_path)
        
        # Staging tables: VACUUM only
        elif table_name.startswith("stg_"):
            vacuum_table(table_name, table_path, 168)
```

### Dynamic Z-ORDER Selection

```python
def get_optimal_z_order_columns(table_path):
    """Analyze query patterns to determine best Z-ORDER columns"""
    # Get table history
    history = spark.sql(f"""
        DESCRIBE HISTORY delta.`{table_path}`
    """).filter("operation = 'MERGE' OR operation = 'UPDATE'")
    
    # Extract predicates from operations (requires query history parsing)
    # This is a simplified example
    frequent_columns = ["date_key", "customer_key"]  # Derive from actual usage
    
    return frequent_columns[:4]  # Max 4 columns
```

### Cost Optimization

```python
# Run VACUUM less frequently for cold tables
def vacuum_with_frequency(table_name, table_path, last_modified_days):
    """VACUUM only if table modified recently"""
    if last_modified_days <= 7:
        vacuum_table(table_name, table_path, 168)
    else:
        logger.log(table_name, "VACUUM", "SKIPPED", 
                  details=f"Not modified in {last_modified_days} days")
```

---

## Alternatives (Not Recommended)

### ❌ Auto-Optimize (`delta.autoOptimize.optimizeWrite`)

**Why Not**:
- Slows down every write operation (20-40% overhead)
- Unpredictable compute costs
- Not suitable for batch workloads
- Better for streaming scenarios only

**Use Case**: Only enable for streaming tables with continuous ingestion

### ❌ Third-Party Orchestration (Azure Automation, Logic Apps)

**Why Not**:
- Adds unnecessary complexity
- Additional authentication layers
- Fabric pipelines provide native integration
- More failure points

**Exception**: Multi-cloud environments requiring cross-platform orchestration

### ❌ Manual Execution

**Why Not**:
- Human error prone
- Inconsistent execution
- No audit trail
- Scheduling gaps

**Exception**: One-time emergency maintenance only

---

## Pre-Implementation Checklist

- [ ] Verify lakehouse path resolution (`lh_gold_path` variable set)
- [ ] Set appropriate retention hours (168 minimum)
- [ ] Configure Z-ORDER columns for key tables
- [ ] Define exclude list for non-production tables
- [ ] Test with `dry_run = True` first
- [ ] Validate Fabric capacity has sufficient CUs
- [ ] Set up pipeline with appropriate timeout
- [ ] Configure failure notifications
- [ ] Create `_maintenance_logs` table for tracking
- [ ] Schedule during low-usage window
- [ ] Document table-specific maintenance requirements
- [ ] Test rollback procedure (time travel)

---

## Post-Implementation Validation

### Week 1: Immediate Validation

```sql
-- Verify maintenance ran successfully
SELECT * FROM gold._maintenance_logs 
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS;

-- Check table file counts (should decrease after OPTIMIZE)
DESCRIBE DETAIL delta.`{table_path}`;

-- Validate query performance improvement
-- Run baseline queries and compare execution times
```

### Month 1: Performance Analysis

- Compare query durations (pre vs. post maintenance)
- Monitor storage costs (should decrease via VACUUM)
- Track CU consumption during maintenance windows
- Analyze failure patterns and adjust configuration

### Quarterly Review

- Reassess Z-ORDER columns based on query patterns
- Evaluate partition strategy for large tables
- Review retention period requirements
- Optimize maintenance schedule based on usage patterns

---

## References

**Official Documentation**:
- [Delta Lake Optimization](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order)
- [OPTIMIZE Command](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order?tabs=sparksql#optimize)
- [VACUUM Command](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order?tabs=sparksql#vacuum)
- [Z-ORDER BY](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order?tabs=sparksql#z-order-by)
- [Fabric Pipeline Scheduling](https://learn.microsoft.com/en-us/fabric/data-factory/pipeline-runs)

**Best Practices**:
- [Delta Lake Best Practices](https://docs.delta.io/latest/best-practices.html)
- [Fabric Capacity Management](https://learn.microsoft.com/en-us/fabric/enterprise/licenses)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-18 | Initial production release |

---

**Maintained by**: Data Engineering Team  
**Last Updated**: 2025-11-18  
**Next Review**: 2026-02-18
