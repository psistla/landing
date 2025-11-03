
---

Summary recommendations (quick)

1. Enable Starter Pools in both workspaces (F32 & F64) — fastest session startup (seconds). 


2. Turn on High Concurrency mode at workspace-level and use session tags for notebook runs that should share sessions — reduces repeated startup time when running notebooks in parallel. 


3. Create suitable Spark pools (or tune existing pools) per SKU (smaller pool for F32, larger for F64) and set sensible executor/memory bounds in Workspace → Spark Compute. 


4. Use a utilities notebook that sets only session-level Spark properties via spark.conf.set(...) (idempotent) before workload code — include shuffle / adaptive / delta write / small-file controls. (Code below.) 




---

Where to change workspace / pool settings (step-by-step)

Follow these steps for each workspace (F32 and F64). Admin role required.

1. In Fabric portal, open the workspace → Workspace settings → Data engineering / Spark (or Spark Compute). This is where pools and workspace-level Spark defaults live. 


2. Enable Starter Pools (recommended for development and fast interactive sessions). If you already have custom pools for production, keep them but add a Starter Pool for notebooks and ad-hoc work. Starter pools give 5–10s session startup. 

For F32: choose smaller starter pool sizes (fewer cores per executor) so concurrency limits (cores) are respected.

For F64: you can allocate bigger executor sizes or an additional custom pool for heavy ETL.



3. Set High Concurrency mode at workspace level (if available in your Fabric release). This enables session reuse across notebook runs when you use session tags — critical when you schedule many notebooks in parallel. Add a default concurrency policy if present. 


4. Configure pool sizing: Open the pool details and choose number of executors / cores / memory per executor within the SKU limits. Use the Fabric UI’s compute sizing controls (you’ll see allowed ranges). For predictable performance, avoid extremely small executors or extremely large ones — tune to workload. 


5. Optional: Set workspace-level Spark defaults (if you want some properties applied by default) — but prefer session-level spark.conf.set() in your utilities notebook so scheduled jobs are portable. 




---

Concurrency & quotas — what to watch for

Fabric enforces cores-based throttling and simple FIFO queueing based on SKU capacity. If you run many notebooks concurrently you’ll hit queueing limits. Use session tags + high concurrency to reduce session starts and CPU/core consumption. For production heavy workloads, push into F64 or dedicated pools. 



---

Utilities notebook — copy-paste code (idempotent)

Run this at the top of your notebooks or as a scheduled utilities notebook that other pipelines reference. It sets session-level properties only (doesn't change cluster/pool definitions). Adjust numeric values to your workload (comments explain each). This is Python PySpark code for Fabric notebooks.

# Utilities: Fabric Spark session settings (idempotent)
# Run at the start of a notebook or as a pre-flight utilities notebook that other jobs import.
# Adjust numbers (partitions, memory fractions, target sizes) to match your dataset sizes and pool capacity.

# 1) Basic runtime flags
spark.conf.set("spark.sql.adaptive.enabled", "true")                       # enable AQE -> adapt shuffle partitions at runtime
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", str(128 * 1024 * 1024))  # target ~128 MB partitions

# 2) Shuffle / join tuning (reduce too many small files/shuffle partitions)
spark.conf.set("spark.sql.shuffle.partitions", "200")                      # default; override based on cluster cores
# If your pool has N cores available to the job, set partitions ~ 2-4 * total cores for good parallelism.

# 3) Memory / serialization / broadcast
spark.conf.set("spark.sql.inMemoryColumnarStorage.compressed", "true")
spark.conf.set("spark.sql.inMemoryColumnarStorage.batchSize", "10000")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))  # 10MB broadcast threshold; tune as needed

# 4) Delta / write optimization (reduce small files)
# Enable OptimizeWrite if available in your Fabric/Delta runtime — reduces number of small files.
# Fabric supports Delta optimize-style options; set conservative defaults.
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.targetFileSize", str(128 * 1024 * 1024))

# 5) Adaptive execution tuning to help data skew
spark.conf.set("spark.sql.adaptive.skewedPartitionThresholdInBytes", str(256 * 1024 * 1024))
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", str(128 * 1024 * 1024))

# 6) Task retry/attempts and logging (practical defaults)
spark.conf.set("spark.task.maxFailures", "4")
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")      # safe overwrite by partition

# 7) Execution behavior for interactive notebooks
# When using session tags and high-concurrency, keep sessions alive for shorter time to free capacity
spark.conf.set("spark.sql.ui.retainedJobs", "200")

# 8) Optional: limit parallelism for certain ad-hoc jobs to avoid taking entire pool (uncomment to use)
# spark.conf.set("spark.executor.instances", "4")
# spark.conf.set("spark.executor.cores", "2")

# Print out a short summary to logs (helpful in notebooks)
print("Applied Fabric session spark.conf settings:")
print(spark.sparkContext.getConf().getAll())

Notes on the code:

The spark.databricks.delta.* keys are recognized in Delta-enabled Fabric runtime as "optimize write / auto compact" features — these reduce the number of files and improve write performance; if your Fabric runtime has slightly different keys, the settings are harmless (they'll be ignored) but check workspace defaults if you rely on them. (See Delta optimize-write guidance). 

spark.sql.shuffle.partitions default needs tuning per pool cores. For development in F32, pick smaller (# partitions 50–200). For F64 heavy ETL, increase (# partitions 200–1000) aligned to cores. 



---

Step-by-step process (exact actions you or admin will perform)

For F32 workspace (dev / interactive)

1. As workspace admin: Workspace → Workspace settings → Data Engineering → Spark Compute. Create or enable a Starter Pool sized modestly (e.g., small vCPU per executor). Enable High concurrency for the workspace if available. 


2. Ensure pool CPU/cores limits suit many small interactive jobs (since F32 has lower total cores). Use starter pool for notebooks: fast start, lightweight resources. 


3. Use the utilities notebook above as the first cell or run it as scheduled preflight to set session properties. Schedule it to run before a batch of notebooks if you want guaranteed session pre-warming (but using session tags and high concurrency is preferred). 



For F64 workspace (prod / heavy ETL)

1. Workspace → Spark Compute → Create a custom pool with larger cores/memory per executor; or tune existing pool to allocate more memory/cores per executor. Keep a starter pool for fast interactive debug sessions. 


2. Keep production ETL jobs pointed to this custom pool. Use the same utilities notebook (with possibly larger spark.sql.shuffle.partitions and targetFileSize) to tune for throughput. 




---

Why each setting matters (short)

Starter pools: pre-provisioning nodes for interactive sessions — session starts in seconds vs minutes. Great for notebooks. 

High Concurrency + session tags: share sessions across multiple notebook runs so you don’t repeatedly pay the session-start cost when many notebooks run in parallel. This reduces cumulative latency. 

AQE (Adaptive Query Exec): lets Spark dynamically reduce/increase shuffle partitions and handle skew — often provides big wins without manual tuning. 

Shuffle partitions tuning: prevents creating thousands of tiny partitions or too few large partitions — both extremes hurt perf. Align partitions to cores. 

Delta optimize/autoCompact: reduces small files on writes (esp. bronze → silver writes), improving read throughput for subsequent downstream jobs. 



---

Additional best practices (practical)

Use session tags in your pipelines/notebooks when launching (e.g., sessionTag: "daily-ingest") — that helps Fabric reuse sessions. (Fabric docs reference session tags in high-concurrency context.) 

Avoid Python UDFs when possible — prefer built-in Spark SQL or vectorized Pandas UDFs; Python UDFs are slow.

Partition and bucket your large tables on logical keys (date, region) to speed reads and avoid full scans.

Compact delta tables regularly (optimize + Z-ORDER for frequently filtered columns) to improve large read queries. 

Monitor job logs and long-running tasks — tune executor size vs number to avoid GC pressure. Use Fabric monitoring and driver/executor logs.

File sizes: aim for ~128MB per parquet/delta file on writes (hence targetFileSize in settings). Too many small files hurts metadata and read performance. 



---

Troubleshooting & validation steps

1. After applying workspace pool changes, open a notebook and run a quick spark.range(1).count() to observe session startup time. If still slow, confirm starter pool enabled and pool has available capacity. 


2. Run spark.conf.get("spark.sql.shuffle.partitions") inside notebook to confirm utilities notebook applied settings.


3. Use Fabric job and pool metrics to see queuing or cores throttling (if many jobs queue, consider fewer concurrent notebooks or larger SKU). 




---

Quick checklist you can run right now

[ ] Workspace admin: enable Starter pools in both F32 and F64. 

[ ] Turn on High Concurrency and start using session tags. 

[ ] Create or tune pools (F32: smaller executors/higher concurrency; F64: larger executors for throughput). 

[ ] Add the utilities notebook as the first step in pipeline runs or import it into each notebook. Use the code above.

[ ] Schedule compact/optimize jobs on Delta tables (silver/gold) to control small files. 



---

Sources / verify

Configure and manage Starter Pools in Microsoft Fabric. 

What is Apache Spark compute in Microsoft Fabric? (starter pools note). 

Spark compute configuration settings in Fabric environments (pool tuning in UI). 

Concurrency throttling and queueing in Spark for Fabric. 

Delta / Optimize Write guidance (small file handling). 

Spark SQL tuning & AQE docs (general Spark guidance). 



---
