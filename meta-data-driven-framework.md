
---

# **Metadata-Driven Framework with Medallion Architecture in Microsoft Fabric: Comprehensive Guide**

## **Overview**

The medallion lakehouse architecture is a design pattern used by organizations to logically organize data in a lakehouse and is the recommended design approach for Microsoft Fabric. It comprises three distinct layers: bronze (raw data), silver (validated data), and gold (enriched data), where each layer indicates the quality of data stored, with higher levels representing higher quality [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture) .

Metadata-driven pipelines in Microsoft Fabric give you the capability to ingest and transform data with less code, reduced maintenance and greater scalability than writing code or pipelines for every data source. The key lies in identifying the data loading and transformation pattern(s) for your data sources and destinations and then building the framework to support each pattern [Microsoft Community Hub](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/metadata-driven-pipelines-for-microsoft-fabric/3891651) .

---

## **Core Architecture Components**

### **1. Medallion Architecture Layers**

**Bronze Layer (Raw Zone)**
The bronze zone stores data in the same format as the data source. When the data source is a relational database, Delta tables are a good choice [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture) . 

Key characteristics:
- Stores raw, unprocessed data exactly as received from sources
- Minimal data validation is performed, with most fields stored as string, VARIANT, or binary to protect against unexpected schema changes [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- Metadata columns might be added, such as the provenance or source of the data (for example, _metadata.file_name) [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- Serves as the historical record and enables data replay

**Silver Layer (Validated Zone)**
Data cleanup and validation are performed in this layer, including dropping nulls and quarantining invalid records. Datasets are joined into new datasets for predictive analytics and enhanced with additional information [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion) .

Key characteristics:
- Performs data cleansing, deduplication, and normalization [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- Implements business rules and quality checks
- Creates enterprise-wide, standardized data models
- Reads should be configured as streaming reads from bronze for append-only sources, with batch reads reserved for small datasets [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)

**Gold Layer (Enriched Zone)**
The consumption-ready layer optimized for business analytics and reporting.

Key characteristics:
- Contains aggregated, business-level tables
- Optimized for specific analytical use cases
- Powers dashboards, reports, and ML models
- Can be implemented as either Lakehouse or Data Warehouse

### **2. Metadata-Driven Framework Components**

Key components used in building the metadata-driven lakehouse implementation include data ingestion, data validation, profiling, transformation, and auditing modules [Microsoft Fabric](https://blog.fabric.microsoft.com/en/blog/playbook-for-metadata-driven-lakehouse-implementation-in-microsoft-fabric/) .

**Control Tables**
The main control table stores the table list, file path or copy behaviors. The connection control table stores the connection value of your data store if you used parameterized linked service [Microsoft Learn](https://learn.microsoft.com/en-us/azure/data-factory/copy-data-tool-metadata-driven) .

Essential control tables include:
- **Ingest_Control**: Source/target mappings, connection strings, load types (full/incremental)
- **Silver_Control**: Transformation rules, data quality checks, business logic
- **Gold_Control**: Aggregation rules, SCD type configurations
- **DQ_Rules_Assignment**: Data quality validation rules
- **Audit Tables**: Job execution tracking, success/failure logging, performance metrics

**Orchestration Pipelines**
The orchestrator pipeline contains a Lookup activity on the Source to Bronze configuration table to get the list of tables to load from source to Bronze. For each table defined in the Lookup activity, call a child pipeline to load the data, passing in the configuration detail from the lookup [Microsoft Community Hub](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/metadata-driven-pipelines-for-microsoft-fabric/3891651) .

---

## **Implementation Guide**

### **Step 1: Infrastructure Setup**

To implement medallion architecture in Fabric, you can either use lakehouses (one for each zone), a data warehouse, or combination of both [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture) .

**Recommended Patterns:**
- **Pattern 1**: Create each zone (Bronze, Silver, Gold) as a Lakehouse
- **Pattern 2**: Create the bronze and silver zones as lakehouses, and the gold zone as a data warehouse [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)

**Workspace Strategy:**
Generally, one workspace is sufficient for managing the Bronze, Silver, and Gold layers within the Medallion Architecture. This simplifies data lineage tracking, access control, and administration [Microsoft Community](https://community.fabric.microsoft.com/t5/Fabric-platform/Implementing-Medallion-Architecture-in-Fabric/td-p/3757738) .

However, separate workspaces may be needed when:
- You have complex governance requirements with strict separation of duties or are working with highly sensitive data that demands isolation for specific layers [Microsoft Community](https://community.fabric.microsoft.com/t5/Fabric-platform/Implementing-Medallion-Architecture-in-Fabric/td-p/3757738)

### **Step 2: Control Table Design**

```sql
-- Example Bronze Control Table Structure
CREATE TABLE bronze_control (
    source_id INT,
    source_name VARCHAR(100),
    source_type VARCHAR(50), -- Database, API, File
    connection_string VARCHAR(500),
    schema_name VARCHAR(100),
    table_name VARCHAR(100),
    load_type VARCHAR(20), -- Full, Incremental
    watermark_column VARCHAR(100),
    target_path VARCHAR(500),
    is_active BIT,
    priority INT,
    last_load_datetime DATETIME
)

-- Example Silver Control Table
CREATE TABLE silver_control (
    transformation_id INT,
    source_layer VARCHAR(50),
    source_table VARCHAR(200),
    target_table VARCHAR(200),
    transformation_logic TEXT,
    dq_rules VARCHAR(500),
    scd_type INT,
    business_keys VARCHAR(500),
    is_active BIT
)
```

### **Step 3: Build Metadata-Driven Pipelines**

**Parent Pipeline (Orchestrator)**
```
1. Lookup Activity → Query control table for active sources
2. ForEach Activity → Iterate through each source
   └─ Execute Child Pipeline (pass parameters)
3. Update Audit Table → Log completion status
```

**Child Pipeline (Worker)**
```
1. Read parameters from parent
2. Set dynamic connection using metadata
3. Execute Copy/Transform activity
4. Handle errors and retry logic
5. Update watermark/audit information
```

A selection predicate based upon date is needed for incremental loads from the source. If the load type setting from the configuration table is a full load, do a Copy Data Activity from the Source to Bronze Lakehouse Delta Lake Table [Microsoft Community Hub](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/metadata-driven-pipelines-for-microsoft-fabric/3891651) .

### **Step 4: Implement Transformations**

**Using Notebooks (PySpark)**
```python
# Silver Layer Transformation Example
from pyspark.sql.functions import *

# Read control table
control_df = spark.sql("SELECT * FROM silver_control WHERE is_active = 1")

for row in control_df.collect():
    # Read from Bronze
    bronze_df = spark.table(f"bronze.{row.source_table}")
    
    # Apply transformations
    silver_df = (bronze_df
        .dropDuplicates(row.business_keys.split(','))
        .na.drop(subset=row.required_columns.split(','))
        .withColumn("load_date", current_timestamp())
    )
    
    # Apply DQ rules
    if row.dq_rules:
        silver_df = apply_dq_rules(silver_df, row.dq_rules)
    
    # Write to Silver
    (silver_df.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(f"silver.{row.target_table}")
    )
```

**Using SQL (T-SQL in Warehouse)**
```sql
-- Gold Layer Aggregation
MERGE INTO gold.sales_summary AS target
USING (
    SELECT 
        customer_id,
        product_category,
        SUM(sales_amount) as total_sales,
        COUNT(*) as transaction_count,
        CURRENT_TIMESTAMP as last_updated
    FROM silver.sales_transactions
    WHERE load_date > GETDATE() - 1
    GROUP BY customer_id, product_category
) AS source
ON target.customer_id = source.customer_id 
   AND target.product_category = source.product_category
WHEN MATCHED THEN UPDATE SET
    total_sales = source.total_sales,
    transaction_count = source.transaction_count,
    last_updated = source.last_updated
WHEN NOT MATCHED THEN INSERT VALUES (
    source.customer_id, 
    source.product_category, 
    source.total_sales,
    source.transaction_count,
    source.last_updated
);
```

### **Step 5: Advanced Features**

**New: Materialized Lake Views (Preview)**
Materialized Lake views (MLV) in Microsoft Fabric allow you to build declarative data pipelines using SQL, complete with built-in data quality rules and automatic monitoring of data transformations. An MLV is a persisted, continuously updated view of your data that simplifies how you implement multi-stage Lakehouse processing [Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/announcing-materialized-lake-views-at-build-2025/) .

**Real-Time Intelligence Integration**
Building a multi-layer, medallion architecture using Fabric Real-Time Intelligence (RTI) requires a different approach. Real-Time Intelligence allows you to build a medallion architecture by processing the data as it arrives, enabling you to build your Bronze, Silver, and Gold layers while maintaining the real-time aspect of your data [Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/21597/) .

---

## **Examples & Real-World Implementation**

### **Case Study: Small-Medium Enterprise Success**

A company of around 200 employees successfully implemented this project with a very small team: 1 data engineer and 3 data analysts, maintaining the project with a low monthly cost using F4 Fabric capacity. The implementation empowered business areas to perform their own analyses, enhanced data governance, and laid the foundation for a data-driven strategy [Medium](https://medium.com/@tiagocardoso1/implementing-medallion-architecture-in-microsoft-fabric-a-real-case-example-3efdeab7f68f) .

**Data Sources Integrated:**
- NoSQL (MongoDB) for telemetry data
- SQL Server as ERP production database
- REST APIs for digital products data

**Implementation Approach:**
- Each layer was defined as a separate Workspace. Bronze layer ingested all data as raw as possible, keeping history for reprocessing or data recovery. Silver layer automated minor general transformations such as detecting and excluding empty or single-value columns, correcting data types, and checking for possible duplicated data [Medium](https://medium.com/@tiagocardoso1/implementing-medallion-architecture-in-microsoft-fabric-a-real-case-example-3efdeab7f68f)

---

## **Pros and Cons**

### **Advantages**

**1. Scalability & Maintainability**
- You can maintain (add/remove) the objects list to be copied easily by just updating the object names in control table instead of redeploying the pipelines [Microsoft Learn](https://learn.microsoft.com/en-us/azure/data-factory/copy-data-tool-metadata-driven)
- Metadata-driven pipeline approaches help save time, cost, and ultimately increase productivity. They provide scalability, reusability, unified code, and many more benefits [Medium](https://medium.com/@meetalpa/how-to-implement-a-metadata-driven-azure-data-factory-pipeline-or-azure-synapse-data-integration-cc1c8e02ab2d)

**2. Code Reusability**
- Single pipeline handles multiple sources
- Reduced code duplication across projects
- Centralized transformation logic

**3. Operational Excellence**
- Comprehensive audit trails ensure consistency and help with version control of both the code and business logic, holding all parties accountable [Infinitive](https://infinitive.com/metadata-driven-framework-data-pipelines/)
- Single control plane for monitoring
- Simplified debugging and troubleshooting

**4. Governance & Compliance**
- Medallion architecture guarantees atomicity, consistency, isolation, and durability (ACID) as data progresses through the layers [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- Centralized data quality management
- Clear data lineage

**5. Flexibility**
- If you need to build similar pipelines for multiple data sources, the same framework can read different metadata configurations to generate a new pipeline for each source [Infinitive](https://infinitive.com/metadata-driven-framework-data-pipelines/)
- Easy to adapt to changing requirements
- Multiple technology options (Spark, SQL, Data Pipelines)

### **Disadvantages**

**1. Initial Complexity**
- While metadata-driven, automated ETL pipeline creation sounds appealing, it may introduce maintenance overhead and struggle to scale efficiently when the complexity of the transformation process varies too much [Databricks](https://community.databricks.com/t5/technical-blog/metadata-driven-etl-framework-in-databricks-part-1/ba-p/92666)
- Requires significant upfront design and planning
- Learning curve for development teams

**2. Over-Engineering Risk**
- Can become unnecessarily complex for simple use cases
- May not be suitable for one-off or rarely changing pipelines
- If you try to jump directly into the parameterization and fetching of metadata, the solution might get too complex too fast and it's harder to debug [Red Gate Software](https://www.red-gate.com/simple-talk/databases/sql-server/bi-sql-server/how-to-build-metadata-driven-pipelines-in-microsoft-fabric/)

**3. Performance Considerations**
- Performance degradation occurs when the compute engine has many metadata and file operations to manage. For better query performance, aim for data files that are approximately 1 GB in size [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- Additional overhead from control table queries
- Potential bottlenecks in orchestration layer

**4. Tight Coupling**
- Dependence on control table schema
- Changes to metadata structure require framework updates
- Potential single point of failure

**5. Limited Transformation Complexity**
- Works best for standardized patterns
- Complex, highly customized transformations may not fit the framework
- May require hybrid approach (metadata-driven + custom code)

---

## **Complexity Analysis**

### **Development Complexity: Medium to High**

**Component Breakdown:**
1. **Control Table Design**: Medium - Requires understanding of all data patterns
2. **Pipeline Orchestration**: Medium - Standard patterns, well-documented
3. **Error Handling**: High - Must handle diverse failure scenarios
4. **Monitoring & Auditing**: Medium - Built-in Fabric capabilities help
5. **Performance Tuning**: High - Requires expertise in Delta Lake optimization

### **Operational Complexity: Low to Medium**

Once implemented:
- Adding new sources is simple (control table update)
- Monitoring is centralized
- Common issues are easier to diagnose
- Standard troubleshooting procedures

---

## **Common Pitfalls & How to Avoid Them**

### **1. Small File Problem**
**Pitfall**: Performance degradation occurs when the compute engine has many metadata and file operations to manage [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)

**Solution**:
- Delta Lake has a feature called predictive optimization that automates maintenance operations for Delta tables [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- Implement file compaction strategies
- Target ~1GB file sizes
- Use auto-optimize features

### **2. Schema Evolution Issues**
**Pitfall**: If you write directly from ingestion, you'll introduce failures due to schema changes or corrupt records in data sources [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)

**Solution**:
- Store most fields as string, VARIANT, or binary in Bronze layer to protect against unexpected schema changes [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- Implement schema validation in Silver layer
- Use Delta Lake schema evolution capabilities

### **3. Direct Silver Writes**
**Pitfall**: Writing directly to Silver from ingestion sources

**Solution**:
- Azure Databricks does not recommend writing to silver tables directly from ingestion as you'll introduce failures due to schema changes or corrupt records. Always land data in Bronze first [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)

### **4. Over-Parameterization**
**Pitfall**: Making everything metadata-driven, even simple transformations

**Solution**:
- Start simple with hardcoded pipeline first
- Create a pipeline that copies one single table and everything's hardcoded. If you try to jump directly into the parameterization, the solution might get too complex too fast and it's harder to debug [Red Gate Software](https://www.red-gate.com/simple-talk/databases/sql-server/bi-sql-server/how-to-build-metadata-driven-pipelines-in-microsoft-fabric/)
- Gradually add parameterization where it adds value

### **5. Inadequate Error Handling**
**Pitfall**: Failures cascade across entire framework

**Solution**:
- Implement retry logic with exponential backoff
- Quarantine bad records rather than failing entire pipeline
- The framework includes metadata for error handling, specifying actions if an error occurs, such as logging it in a separate table or triggering an alert [Infinitive](https://infinitive.com/metadata-driven-framework-data-pipelines/)

### **6. Poor Performance Due to File Retention**
**Pitfall**: Excessive historical data accumulation

**Solution**:
- Based on your business requirements, keep historical data only for a certain period of time to reduce storage costs. Consider retaining historical data for only the last month, or other appropriate period of time using the VACUUM command [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- Configure delta.deletedFileRetentionDuration appropriately

### **7. Workspace Organization**
**Pitfall**: All layers in single workspace causing governance issues

**Solution**:
- While you can create all lakehouses in a single Fabric workspace, we recommend that you create each lakehouse in its own, separate workspace [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture) for complex scenarios
- Balance simplicity vs. governance requirements

### **8. Incremental Load Logic Errors**
**Pitfall**: Missing or duplicate data due to watermark issues

**Solution**:
- Implement proper watermark tracking
- Use transactional updates to control tables
- Validate data completeness after each load

---

## **Success Rate & Adoption**

While specific success rate statistics aren't publicly available, several indicators suggest strong adoption:

### **Industry Adoption Signals**

1. **Microsoft Recommendation**: Medallion architecture is the recommended design approach for Fabric [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)

2. **Gartner Prediction**: Gartner predicts 70% of organizations will shift from batch to streaming architectures by 2025 [DynaTech Consultancy](https://dynatechconsultancy.com/blog/medallion-architecture-in-microsoft-fabric)

3. **Real-World Success**: The implementation was successful with a very small team (1 data engineer, 3 data analysts) maintaining it with low monthly cost (F4 Fabric capacity), demonstrating it is possible for non-IT core businesses or small/middle companies to improve their data quality and move to a data-driven strategy [Medium](https://medium.com/@tiagocardoso1/implementing-medallion-architecture-in-microsoft-fabric-a-real-case-example-3efdeab7f68f)

### **Success Factors**

**High Success Probability When:**
- Team has clear understanding of data patterns
- Proper investment in initial design phase
- Standardized data sources and transformation patterns
- Strong governance requirements
- Need to scale to many data sources
- The framework is consistent with a consistent template that developers can utilize, modular with reusable components, scalable to support different layers, auditable and traceable, and seamlessly integrated with CI-CD practices [Databricks](https://community.databricks.com/t5/technical-blog/metadata-driven-etl-framework-in-databricks-part-1/ba-p/92666)

**Lower Success Probability When:**
- Highly heterogeneous transformation requirements
- Frequently changing business logic
- Small number of data sources (overhead may not justify complexity)
- Lack of technical expertise in the team
- Insufficient planning and design phase

---

## **Best Practices for Implementation**

### **1. Start Simple, Scale Gradually**
When you want to create a metadata driven framework, it's always a good idea to start easily. You create a pipeline that copies one single table and everything's hardcoded, then gradually implement parameterization [Red Gate Software](https://www.red-gate.com/simple-talk/databases/sql-server/bi-sql-server/how-to-build-metadata-driven-pipelines-in-microsoft-fabric/)

### **2. Implement Comprehensive Auditing**
Audit tables in an ETL framework are essential for tracking the success, failure, and performance of data processes, ensuring data integrity and transparency. They provide crucial logging information for troubleshooting and compliance [Databricks](https://community.databricks.com/t5/technical-blog/metadata-driven-etl-framework-in-databricks-part-1/ba-p/92666)

### **3. Follow Standard Patterns**
- Full load vs. incremental load patterns
- SCD Type 1, 2, and 3 implementations
- Error handling and retry mechanisms
- Data quality validation checkpoints

### **4. Optimize Performance**
- Fabric can optimize data files during data write. For more information, see Predictive optimization for Delta Lake [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- Use appropriate partitioning strategies
- Implement data lifecycle management

### **5. Enable Proper Governance**
- You can create a data mesh architecture for your data estate in Fabric by creating data domains. You might create domains that map to your business domains, for example, marketing, sales, inventory, human resources, and implement medallion architecture by setting up data zones within each of your domains [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)

### **6. Leverage Fabric-Specific Features**
- Use OneLake for unified data storage
- Implement Direct Lake for Power BI reporting
- Utilize Shortcuts to avoid data duplication
- Take advantage of cross-workspace lineage

---

## **Monitoring & Maintenance**

### **Key Metrics to Track**
1. **Pipeline Performance**
   - Execution duration per layer
   - Data volume processed
   - Success/failure rates

2. **Data Quality**
   - Validation rule pass/fail rates
   - Rejected record counts
   - Data completeness metrics

3. **Resource Utilization**
   - Compute capacity consumption
   - Storage growth rates
   - Cost per workload

4. **Operational Health**
   - SLA compliance
   - Average time to recovery
   - Incident frequency

---

## **Conclusion**

The metadata-driven framework with medallion architecture in Microsoft Fabric represents a powerful, scalable approach to modern data platform implementation. Implementing a metadata-driven Lakehouse using Microsoft Fabric enables organizations to efficiently manage and process data with governance, scalability, and optimal performance [Microsoft Fabric](https://blog.fabric.microsoft.com/en/blog/playbook-for-metadata-driven-lakehouse-implementation-in-microsoft-fabric/) .

**When to Use This Approach:**
- ✅ Managing multiple data sources with similar patterns
- ✅ Need for centralized governance and auditing
- ✅ Scaling to dozens or hundreds of data entities
- ✅ Standardized transformation logic across sources
- ✅ Strong compliance and traceability requirements

**When to Consider Alternatives:**
- ❌ Very few data sources (< 10)
- ❌ Highly customized, complex transformations per source
- ❌ One-off or rarely changing data flows
- ❌ Limited technical resources for framework maintenance
- ❌ Simple, straightforward ETL requirements

The key to success lies in proper planning, starting simple, iterating based on learnings, and maintaining a balance between standardization and flexibility. Organizations should invest adequately in the design phase, ensure team training, and implement comprehensive monitoring from day one.

Citations:
- [Implement medallion lakehouse architecture in Fabric - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture)
- [Metadata Driven Pipelines for Microsoft Fabric | Microsoft Community Hub](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/metadata-driven-pipelines-for-microsoft-fabric/3891651)
- [What is the medallion lakehouse architecture? - Azure Databricks | Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- [Playbook for metadata driven Lakehouse implementation in Microsoft Fabric | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en/blog/playbook-for-metadata-driven-lakehouse-implementation-in-microsoft-fabric/)
- [Build large-scale data copy pipelines with metadata-driven approach in copy data tool - Azure Data Factory | Microsoft Learn](https://learn.microsoft.com/en-us/azure/data-factory/copy-data-tool-metadata-driven)
- [Solved: Implementing Medallion Architecture in Fabric - Microsoft Fabric Community](https://community.fabric.microsoft.com/t5/Fabric-platform/Implementing-Medallion-Architecture-in-Fabric/td-p/3757738)
- [Simplifying Medallion Implementation with Materialized Lake Views in Fabric | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-us/blog/announcing-materialized-lake-views-at-build-2025/)
- [Medallion Architecture in Fabric Real-Time Intelligence | Microsoft Fabric Blog | Microsoft Fabric](https://blog.fabric.microsoft.com/en-US/blog/21597/)
- [Implementing Medallion Architecture in Microsoft Fabric: a real case example | by Tiago Cardoso | Medium](https://medium.com/@tiagocardoso1/implementing-medallion-architecture-in-microsoft-fabric-a-real-case-example-3efdeab7f68f)
- [How to implement a Metadata driven Azure Data Factory Pipeline or Azure Synapse Data Integration Pipeline? | by alpa buddhabhatti | Medium](https://medium.com/@meetalpa/how-to-implement-a-metadata-driven-azure-data-factory-pipeline-or-azure-synapse-data-integration-cc1c8e02ab2d)
- [The Infinitive Metadata-driven Framework for Generating Data Pipelines in Databricks](https://infinitive.com/metadata-driven-framework-data-pipelines/)
- [Metadata-Driven ETL Framework in Databricks (Part-... - Databricks Community - 92666](https://community.databricks.com/t5/technical-blog/metadata-driven-etl-framework-in-databricks-part-1/ba-p/92666)
- [How to Build Metadata Driven Pipelines in Microsoft Fabric - Simple Talk](https://www.red-gate.com/simple-talk/databases/sql-server/bi-sql-server/how-to-build-metadata-driven-pipelines-in-microsoft-fabric/)
- [Medallion Architecture in MS Fabric | DynaTech Systems](https://dynatechconsultancy.com/blog/medallion-architecture-in-microsoft-fabric)

More sources:
- [Organize a Fabric Lakehouse Using Medallion Architecture Design - Training | Microsoft Learn](https://learn.microsoft.com/en-us/training/modules/describe-medallion-architecture/)
- [Create a medallion architecture in a Microsoft Fabric lakehouse | mslearn-fabric](https://microsoftlearning.github.io/mslearn-fabric/Instructions/Labs/03b-medallion-lakehouse.html)
- [How to create a metadata-driven pipeline using Variables](https://www.matillion.com/blog/how-to-create-a-metadata-driven-pipeline-using-variables)
- [(PDF) Metadata-Driven ETL Pipelines: A Framework for Scalable Data Integration Architecture](https://www.researchgate.net/publication/387255336_Metadata-Driven_ETL_Pipelines_A_Framework_for_Scalable_Data_Integration_Architecture)
- [How to Build a Modern Data Pipeline | Best Practices for ETL & System…](https://www.matillion.com/learn/blog/how-to-build-a-data-pipeline)
- [What are Metadata-Driven Pipelines? – Systems, Architecture and Systems Architecture](https://marceloramirez.blog/2023/11/17/what-are-metadata-driven-pipelines/)
- [Creating a Simple Staged Metadata Driven Processing Framework for Azure Data Factory Pipelines – Part 1 of 4](https://mrpaulandrew.com/2020/02/25/creating-a-simple-staged-metadata-driven-processing-framework-for-azure-data-factory-pipelines-part-1-of-4/)
- [Implement medallion architecture in Real-Time Intelligence - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/architecture-medallion)
- [Design Data Warehouse with Medallion Architecture in Microsoft Fabric](https://www.mssqltips.com/sqlservertip/8115/design-data-warehouse-medallion-architecture-microsoft-fabric/)
- [Exploring the Medallion Architecture in Microsoft Fabric | by Mariusz Kujawski | Medium](https://medium.com/@mariusz_kujawski/exploring-the-medallion-architecture-in-microsoft-fabric-f19ad7590293)
- [Lakehouse end-to-end scenario: overview and architecture - Microsoft Fabric | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/tutorial-lakehouse-introduction)
- [Azure-Data-Factory-Workshop/metadata-driven-pipeline.md at main · Microsoft-USEduAzure/Azure-Data-Factory-Workshop](https://github.com/Microsoft-USEduAzure/Azure-Data-Factory-Workshop/blob/main/metadata-driven-pipeline.md)
- [Creating a Simple Staged Metadata Driven Processing Framework for Azure Data Factory Pipelines – Part 2 of 4](https://mrpaulandrew.com/2020/03/02/creating-a-simple-staged-metadata-driven-processing-framework-for-azure-data-factory-pipelines-part-2-of-4/)