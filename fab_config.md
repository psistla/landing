# ðŸ§  Microsoft Fabric Spark Optimization â€“ F32 & F64 Workspaces  
**Author:** ChatGPT (Microsoft Fabric Platform Specialist)  
**Date:** 2025-10-30  

---

## ðŸŽ¯ Context

You have:
- Two Microsoft Fabric workspaces on **F32** and **F64** SKUs.
- A **Medallion Lakehouse** architecture with **Bronze**, **Silver**, and **Gold** layers.
- A goal to make **notebooks start fast**, **run efficiently**, and **support parallel execution**.

---

## âš™ï¸ Spark Configuration via Notebook (Python)

### ðŸ”¹ F32 SKU Configuration
```python
# --- F32 SKU Spark session tuning ---
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Adaptive & dynamic allocation
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", "1")
spark.conf.set("spark.dynamicAllocation.maxExecutors", "8")
spark.conf.set("spark.dynamicAllocation.executorIdleTimeout", "60s")

# Executor and driver settings
spark.conf.set("spark.executor.cores", "2")
spark.conf.set("spark.executor.memory", "6g")
spark.conf.set("spark.executor.memoryOverhead", "0.10")
spark.conf.set("spark.driver.memory", "8g")
spark.conf.set("spark.driver.cores", "2")
spark.conf.set("spark.driver.maxResultSize", "2g")

# Adaptive Query Execution (AQE)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionNum", "8")

# Parallelism & shuffle
spark.conf.set("spark.default.parallelism", "64")
spark.conf.set("spark.sql.shuffle.partitions", "128")

# File & I/O
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")
spark.conf.set("spark.sql.files.openCostInBytes", "4194304")

# Serialization
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
spark.conf.set("spark.kryoserializer.buffer.max", "512m")

# Notebook UX
spark.conf.set("spark.ui.showConsoleProgress", "true")

print("âœ… Spark configuration applied for F32 workspace session.")
```

---

### ðŸ”¹ F64 SKU Configuration
```python
# --- F64 SKU Spark session tuning ---
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Dynamic allocation
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", "1")
spark.conf.set("spark.dynamicAllocation.maxExecutors", "20")
spark.conf.set("spark.dynamicAllocation.executorIdleTimeout", "60s")

# Executor and driver sizing
spark.conf.set("spark.executor.cores", "3")
spark.conf.set("spark.executor.memory", "12g")
spark.conf.set("spark.executor.memoryOverhead", "0.10")
spark.conf.set("spark.driver.memory", "12g")
spark.conf.set("spark.driver.cores", "2")
spark.conf.set("spark.driver.maxResultSize", "4g")

# Adaptive Query Execution
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionNum", "16")

# Parallelism and shuffle tuning
spark.conf.set("spark.default.parallelism", "192")
spark.conf.set("spark.sql.shuffle.partitions", "256")

# File & I/O
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")
spark.conf.set("spark.sql.files.openCostInBytes", "4194304")

# Serialization
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
spark.conf.set("spark.kryoserializer.buffer.max", "512m")

# Interactive UX
spark.conf.set("spark.ui.showConsoleProgress", "true")

print("âœ… Spark configuration applied for F64 workspace session.")
```

---

## ðŸ§© Workspace Setting Dependencies

If you use the Python configs above:
- âœ… **No mandatory workspace setting changes** are required.
- âš™ï¸ But you should **verify** key workspace-level settings for best performance.

---

## ðŸ§± Workspace Settings Verification

| Setting | Location | F32 Recommended | F64 Recommended | Purpose |
|----------|-----------|-----------------|----------------|----------|
| **Starter Pool** | Workspace â†’ âš™ï¸ Settings â†’ *Data Engineering / Data Science* | Enabled<br>Max nodes: 2â€“4 | Enabled<br>Max nodes: 4â€“8 | Fast notebook startup. |
| **Job Concurrency & Queueing** | Workspace â†’ âš™ï¸ Settings â†’ *Job concurrency and queueing* | 3â€“4 concurrent jobs | 6â€“10 concurrent jobs | Prevent queueing and vCore exhaustion. |
| **Custom Spark Pool (optional)** | Workspace â†’ Spark Pools | For heavy ETL | For heavy ETL | Isolates big jobs from interactive work. |
| **Autoscale Billing (optional)** | Workspace â†’ Settings â†’ Billing | Off | Optional | Lets large jobs burst beyond fixed capacity. |

---

## âš™ï¸ Session-Level Config (Per Notebook)

| Task | How | Notes |
|------|------|------|
| Apply tuning | Paste the provided Python config | Per-session only |
| Enable dynamic allocation | Already in config | Allows scaling |
| Enable AQE | Already in config | Optimizes partitioning |
| Keep executor heaps moderate | Default <32GB | Avoids GC stalls |

---

## ðŸ§  Operational & Parallel Execution Best Practices

| Practice | Description | Applies To |
|-----------|--------------|-------------|
| **Parallel notebooks** | Use `runMultiple()` or Fabric pipeline concurrency | All workspaces |
| **Compact small files** | Use Delta `OPTIMIZE` / `VACUUM` | Bronze â†’ Silver â†’ Gold |
| **Monitor vCores** | Fabric Capacity Metrics | Admins |
| **Separate heavy workloads** | Use dedicated pools | Both |
| **Cache only reused data** | Avoid memory bloat | Notebooks |
| **Use broadcast joins** | `broadcast(df_small)` for small tables | Silver/Gold models |

---

## ðŸ“‹ Verification Checklist

âœ… Starter Pool enabled and tuned  
âœ… Job concurrency limits set appropriately  
âœ… Python configs applied successfully  
âœ… Notebook startup < 20s  
âœ… Parallel runs succeed  
âœ… Delta tables compacted regularly  

---

## ðŸ“Š Example Admin Summary

| Workspace | StarterPool | Job Concurrency | Notes |
|------------|--------------|----------------|-------|
| **F32** | âœ… Enabled (max 4 nodes) | 4 concurrent jobs | Used for dev/testing |
| **F64** | âœ… Enabled (max 8 nodes) | 8 concurrent jobs | Used for production |

---

## ðŸ“˜ Summary

- The **Python configs** tune **session-level Spark performance**.  
- The **workspace settings** ensure **fast startup** and **parallel execution**.  
- Use the **Starter Pool** + **dynamic allocation** combo for optimal responsiveness.  
- Monitor **vCore usage** to prevent job queueing.  

Together, these steps make your Fabric Lakehouse workloads efficient and responsive.

---

**End of Markdown Documentation**