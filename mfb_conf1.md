
---

# **Microsoft Fabric Spark Configuration Guide**
## **For F32 & F64 SKUs with Bronze-Silver-Gold Architecture**

---

## **📊 Understanding Your Capacity**

### **F32 Capacity:**
- **Base Spark VCores:** 64 (32 CU × 2)
- **With 3x Burst Factor:** 192 Spark VCores for concurrency
- **Single Job Maximum:** 64 VCores [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-compute) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-job-concurrency-and-queueing)

### **F64 Capacity:**
- **Base Spark VCores:** 128 (64 CU × 2)
- **With 3x Burst Factor:** 384 Spark VCores for concurrency
- **Single Job Maximum:** 128 VCores [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-compute) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-job-concurrency-and-queueing)

**Key Insight:** The burst factor only helps with concurrency, allowing multiple jobs to run simultaneously, but does not increase the maximum cores available for a single Spark job. [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-job-concurrency-and-queueing)

---

## **🎯 STEP-BY-STEP CONFIGURATION**

### **STEP 1: Configure Workspace Settings** 

**Location:** Workspace Settings → Data Engineering/Science → Spark Settings

#### **For Both F32 and F64 Workspaces:**

1. **Pool Type Selection:**
   - **Use Starter Pools** for fast startup (5-10 seconds) - Recommended for development and most production scenarios [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/configure-starter-pools) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-compute)
   - **Custom Pools** only if you need: specific node sizes, Private Links, or Managed VNets [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/create-custom-spark-pools)

2. **Starter Pool Configuration:**
   
   **F32 Workspace:**
   - Max Nodes: **12** (based on capacity limits)
   - Max Executors: **24**
   - Enable Autoscale: **Yes**
   - Enable Dynamic Allocation: **Yes**
   
   **F64 Workspace:**
   - Max Nodes: **24** (based on capacity limits)
   - Max Executors: **48**
   - Enable Autoscale: **Yes**
   - Enable Dynamic Allocation: **Yes**

   **Why:** Starter pools provide pre-provisioned clusters that are always ready, eliminating 2-5 minute wait times for cluster provisioning [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/configure-starter-pools)

3. **Session Timeout:**
   - Set to **30 minutes** for interactive sessions
   - **Why:** Default is 20 minutes; 30 minutes reduces unexpected session timeouts during development [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/workspace-admin-settings)

4. **High Concurrency Mode:**
   - **Enable for Bronze/Silver layers** (multiple small transformations)
   - **Disable for Gold layer** (larger, resource-intensive aggregations)
   - **Why:** High concurrency allows multiple notebooks to share a single Spark session, improving resource utilization for smaller jobs [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/configure-high-concurrency-session-notebooks)

5. **Customize Compute Configuration:**
   - Enable this setting
   - **Why:** Allows users to adjust compute properties per notebook/environment for flexibility [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/workspace-admin-settings)

---

### **STEP 2: Create Utilities Notebook**

Create a notebook called `config_spark_utilities` that will set optimal Spark configurations for your medallion architecture.

```python
# ============================================================================
# SPARK CONFIGURATION UTILITIES FOR MICROSOFT FABRIC
# For F32/F64 Capacities with Bronze-Silver-Gold Architecture
# ============================================================================

from pyspark.sql import SparkSession

def configure_bronze_layer():
    """
    Bronze Layer Configuration
    Purpose: Fast data ingestion, minimal processing overhead
    """
    print("⚙️ Configuring Bronze Layer Settings...")
    
    # ===== DATA INGESTION OPTIMIZATION =====
    
    # Disable optimize write for bronze - faster ingestion
    spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "false")
    # Why: Bronze layer prioritizes fast writes over read optimization
    
    # Disable V-Order for bronze - reduces write overhead
    spark.conf.set("spark.sql.parquet.vorder.enabled", "false")
    # Why: Bronze doesn't need read optimization; it's a landing zone
    
    # ===== CHECKPOINT OPTIMIZATION =====
    
    # Reduce checkpoint frequency for faster writes
    spark.conf.set("spark.databricks.delta.checkpointInterval", "20")
    # Why: Default is 10; higher value means fewer checkpoints, faster ingestion
    
    # Disable statistics collection for bronze
    spark.conf.set("spark.databricks.delta.collect.stats", "false")
    # Why: Bronze has frequent writes with changing data; stats slow down writes
    
    # ===== FILE SIZE MANAGEMENT =====
    
    # Set target file size for bronze ingestion
    spark.conf.set("spark.sql.files.maxRecordsPerFile", "5000000")
    # Why: Larger files reduce file count, but bronze needs balance for frequent updates
    
    # ===== SHUFFLE OPTIMIZATION =====
    
    # Reduce shuffle partitions for smaller bronze datasets
    spark.conf.set("spark.sql.shuffle.partitions", "100")
    # Why: Default 200 is overkill for bronze; reduces overhead
    
    # ===== MEMORY CONFIGURATION =====
    
    # Set broadcast threshold - don't broadcast large bronze tables
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # 10MB
    # Why: Bronze tables can be large; avoid broadcasting
    
    # Enable adaptive query execution
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    # Why: Automatically optimizes query plans at runtime
    
    print("✅ Bronze Layer Configuration Complete")


def configure_silver_layer():
    """
    Silver Layer Configuration
    Purpose: Data transformation and cleansing with balanced performance
    """
    print("⚙️ Configuring Silver Layer Settings...")
    
    # ===== BALANCED WRITE OPTIMIZATION =====
    
    # Enable optimize write for better file organization
    spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "true")
    # Why: Silver needs balance between write speed and read optimization
    
    # Moderate V-Order for silver
    spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
    # Why: Silver serves analytical queries, V-Order improves read performance
    
    # ===== AUTO COMPACTION =====
    
    # Enable auto-compaction for silver
    spark.conf.set("spark.microsoft.delta.autoCompact.enabled", "true")
    # Why: Automatically merges small files during writes
    
    # ===== STATISTICS AND OPTIMIZATION =====
    
    # Enable statistics for silver
    spark.conf.set("spark.databricks.delta.collect.stats", "true")
    # Why: Silver supports analytical queries; stats improve query planning
    
    # Checkpoint interval for silver
    spark.conf.set("spark.databricks.delta.checkpointInterval", "10")
    # Why: Default value works well for silver's transformation workload
    
    # ===== FILE SIZE MANAGEMENT =====
    
    # Larger file sizes for silver
    spark.conf.set("spark.sql.files.maxRecordsPerFile", "10000000")
    # Why: Silver is more stable; larger files improve read performance
    
    # Target file size for optimize write
    spark.conf.set("spark.microsoft.delta.optimizeWrite.binSize", "512")  # 512MB
    # Why: Good balance for silver transformation workloads
    
    # ===== SHUFFLE OPTIMIZATION =====
    
    # Moderate shuffle partitions
    spark.conf.set("spark.sql.shuffle.partitions", "200")
    # Why: Default works well for silver transformation complexity
    
    # ===== JOIN AND MERGE OPTIMIZATION =====
    
    # Enable low shuffle merge optimization
    spark.conf.set("spark.microsoft.delta.merge.optimizeWrite.enabled", "true")
    # Why: Silver often uses MERGE operations for updates
    
    # Broadcast threshold for silver
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "20971520")  # 20MB
    # Why: Silver may have dimension tables suitable for broadcasting
    
    # ===== ADAPTIVE EXECUTION =====
    
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    # Why: Reduces partition count dynamically after shuffle operations
    
    print("✅ Silver Layer Configuration Complete")


def configure_gold_layer():
    """
    Gold Layer Configuration
    Purpose: Maximum read performance for analytics and reporting
    """
    print("⚙️ Configuring Gold Layer Settings...")
    
    # ===== MAXIMUM READ OPTIMIZATION =====
    
    # Enable optimize write for gold
    spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "true")
    # Why: Gold prioritizes read performance for business users
    
    # Full V-Order optimization
    spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
    # Why: V-Order dramatically improves query performance for Power BI
    
    # ===== AUTO COMPACTION =====
    
    # Enable aggressive auto-compaction
    spark.conf.set("spark.microsoft.delta.autoCompact.enabled", "true")
    # Why: Keeps gold layer optimally organized
    
    # ===== FILE SIZE OPTIMIZATION =====
    
    # Large file sizes for gold
    spark.conf.set("spark.sql.files.maxRecordsPerFile", "20000000")
    # Why: Gold serves reporting; fewer, larger files improve performance
    
    # Large bin size for optimize write
    spark.conf.set("spark.microsoft.delta.optimizeWrite.binSize", "1024")  # 1GB
    # Why: Minimize file count for Power BI Direct Lake performance
    
    # ===== STATISTICS COLLECTION =====
    
    # Enable full statistics
    spark.conf.set("spark.databricks.delta.collect.stats", "true")
    # Why: Gold supports complex analytical queries
    
    # ===== SHUFFLE OPTIMIZATION =====
    
    # Higher shuffle partitions for complex aggregations
    spark.conf.set("spark.sql.shuffle.partitions", "200")
    # Why: Gold often has complex joins and aggregations
    
    # ===== JOIN OPTIMIZATION =====
    
    # Higher broadcast threshold for gold
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "52428800")  # 50MB
    # Why: Gold may have larger dimension tables for star schema
    
    # ===== PREDICATE PUSHDOWN =====
    
    # Enable parquet filter pushdown
    spark.conf.set("spark.sql.parquet.filterPushdown", "true")
    # Why: Reduces data read from parquet files
    
    # ===== ADAPTIVE EXECUTION =====
    
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
    # Why: Handles data skew in gold layer joins automatically
    
    # ===== DIRECT LAKE OPTIMIZATION =====
    
    # Row group size for Direct Lake (Power BI)
    spark.conf.set("spark.sql.parquet.writer.rowGroupSize", "8388608")  # 8MB rows
    # Why: Aligns with Power BI's 8M row segment size for optimal performance
    
    print("✅ Gold Layer Configuration Complete")


def configure_general_optimizations():
    """
    General Optimizations for All Layers
    Purpose: Network, memory, and timeout configurations
    """
    print("⚙️ Configuring General Optimizations...")
    
    # ===== TIMEOUT SETTINGS =====
    
    # Network timeout
    spark.conf.set("spark.network.timeout", "600s")
    # Why: Prevents timeouts on long-running operations
    
    # Broadcast timeout
    spark.conf.set("spark.sql.broadcastTimeout", "600")
    # Why: Prevents broadcast join failures
    
    # ===== DYNAMIC ALLOCATION =====
    
    # Enable dynamic allocation
    spark.conf.set("spark.dynamicAllocation.enabled", "true")
    # Why: Automatically scales executors based on workload
    
    spark.conf.set("spark.dynamicAllocation.minExecutors", "1")
    spark.conf.set("spark.dynamicAllocation.maxExecutors", "20")
    # Why: Starts small, scales as needed
    
    # ===== MEMORY MANAGEMENT =====
    
    # Memory fraction for execution
    spark.conf.set("spark.memory.fraction", "0.8")
    # Why: 80% of memory for execution and storage
    
    # Enable off-heap memory
    spark.conf.set("spark.memory.offHeap.enabled", "true")
    spark.conf.set("spark.memory.offHeap.size", "2g")
    # Why: Reduces garbage collection pressure
    
    # ===== NATIVE EXECUTION ENGINE =====
    
    # Enable Native Execution Engine for performance
    spark.conf.set("spark.sql.execution.arrow.enabled", "true")
    # Why: Uses Apache Arrow for faster data transfer
    
    print("✅ General Optimizations Complete")


def get_current_config():
    """
    Display current Spark configuration
    """
    print("\n📋 Current Spark Configuration:")
    print("=" * 60)
    
    configs_to_check = [
        "spark.microsoft.delta.optimizeWrite.enabled",
        "spark.sql.parquet.vorder.enabled",
        "spark.microsoft.delta.autoCompact.enabled",
        "spark.databricks.delta.checkpointInterval",
        "spark.sql.shuffle.partitions",
        "spark.sql.adaptive.enabled"
    ]
    
    for config in configs_to_check:
        try:
            value = spark.conf.get(config)
            print(f"{config}: {value}")
        except:
            print(f"{config}: Not set")
    
    print("=" * 60)


# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def setup_bronze():
    """Call this function at the start of Bronze layer notebooks"""
    configure_general_optimizations()
    configure_bronze_layer()
    get_current_config()

def setup_silver():
    """Call this function at the start of Silver layer notebooks"""
    configure_general_optimizations()
    configure_silver_layer()
    get_current_config()

def setup_gold():
    """Call this function at the start of Gold layer notebooks"""
    configure_general_optimizations()
    configure_gold_layer()
    get_current_config()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
print("""
📘 USAGE INSTRUCTIONS:

In Bronze notebooks, add to first cell:
    from config_spark_utilities import setup_bronze
    setup_bronze()

In Silver notebooks, add to first cell:
    from config_spark_utilities import setup_silver
    setup_silver()

In Gold notebooks, add to first cell:
    from config_spark_utilities import setup_gold
    setup_gold()
""")
```

---

### **STEP 3: Using the Utilities Notebook**

**Option A: Import in Each Notebook (Recommended)**

```python
# First cell of your Bronze notebook
%run /path/to/config_spark_utilities

setup_bronze()
```

```python
# First cell of your Silver notebook
%run /path/to/config_spark_utilities

setup_silver()
```

```python
# First cell of your Gold notebook
%run /path/to/config_spark_utilities

setup_gold()
```

**Option B: Use Environment Items**

Create Environment items in Fabric for each layer with Spark properties configured, then attach them to notebooks [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/workspace-admin-settings) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/environment-manage-compute)

---

## **📋 ADDITIONAL BEST PRACTICES**

### **1. Parallel Execution**

For running notebooks in parallel, use `mssparkutils.notebook.runMultiple()` with JSON configuration [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/microsoft-spark-utilities)

```python
# Example: Run multiple bronze ingestion notebooks in parallel
from notebookutils.notebook import run_multiple

activities = [
    {"name": "ingest_system1", "path": "/bronze/ingest_system1", "timeoutPerCellInSeconds": 3600},
    {"name": "ingest_system2", "path": "/bronze/ingest_system2", "timeoutPerCellInSeconds": 3600},
    {"name": "ingest_system3", "path": "/bronze/ingest_system3", "timeoutPerCellInSeconds": 3600}
]

run_multiple(activities)
```

### **2. Table Maintenance Strategy**

Run OPTIMIZE and VACUUM operations regularly [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/table-compaction)

```python
# Schedule this notebook to run daily

from delta.tables import DeltaTable

# Gold layer - run daily
for table in ["gold_table1", "gold_table2"]:
    delta_table = DeltaTable.forName(spark, f"gold.{table}")
    delta_table.optimize().executeCompaction()

# Silver layer - run weekly
# Bronze layer - run monthly or as needed
```

### **3. Monitoring Configuration**

```python
# Check Spark session details
def monitor_spark_session():
    print(f"Spark App ID: {spark.sparkContext.applicationId}")
    print(f"Spark Master: {spark.sparkContext.master}")
    print(f"Default Parallelism: {spark.sparkContext.defaultParallelism}")
    print(f"Total Cores: {spark.sparkContext._jsc.sc().getExecutorMemoryStatus().size()}")
```

### **4. F32 vs F64 Considerations**

**F32 Workspace:**
- Suitable for **development, testing, and smaller production workloads**
- Limited to smaller datasets and fewer concurrent users [Microsoft Fabric Community](https://community.fabric.microsoft.com/t5/Service/Power-BI-and-Fabric-what-can-i-do-with-F32-or-lower-capacity-and/m-p/4680701)
- Run fewer parallel jobs (2-3 maximum)

**F64 Workspace:**
- Suitable for **production workloads with higher concurrency**
- Better for larger datasets and more frequent refreshes [Microsoft Fabric Community](https://community.fabric.microsoft.com/t5/Service/Power-BI-and-Fabric-what-can-i-do-with-F32-or-lower-capacity-and/m-p/4680701)
- Can handle 4-6 parallel jobs comfortably

### **5. Session Management**

For notebooks that should always start fresh sessions (Gold layer aggregations), disable high concurrency mode or use session tags [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/configure-high-concurrency-session-notebooks)

---

## **🎯 KEY TAKEAWAYS**

1. **Use Starter Pools** - 5-10 second startup vs 2-5 minutes for custom pools [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/configure-starter-pools) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-compute)

2. **Layer-Specific Configurations**:
   - **Bronze**: Fast writes, minimal overhead
   - **Silver**: Balanced performance
   - **Gold**: Maximum read optimization for reporting

3. **Enable V-Order for Silver/Gold** - Provides up to 50% more compression and 10-50% faster reads [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order)

4. **Regular Maintenance** - Run OPTIMIZE daily on Gold, weekly on Silver [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/table-compaction)

5. **Monitor Capacity Usage** - Use the Capacity Metrics app to track utilization

---

This configuration is production ready!