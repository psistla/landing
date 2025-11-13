

## **Critical Performance Insight**

Chaining multiple `withColumn()` calls creates performance bottlenecks by adding a projection node for each call, which can cause memory issues and even StackOverflowException with [Databricks](https://community.databricks.com/t5/technical-blog/performance-showdown-withcolumn-vs-withcolumns-in-apache-spark/ba-p/129142) [Stack Overflow](https://stackoverflow.com/questions/59789689/spark-dag-differs-with-withcolumn-vs-select) many columns. Using `withColumns()` (Spark 3.3+) or `select()` adds only one projection node regardless of column count, providing 3-4x speedup.

## **Recommended Solution: High-Performance Multi-Column Function**

```python
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit
from pyspark.sql.types import StringType, IntegerType, DoubleType, LongType, BooleanType, DateType, TimestampType
from typing import Dict, Any, Optional, Union

def add_columns(
    df: DataFrame,
    columns_dict: Dict[str, Any],
    data_types: Optional[Dict[str, str]] = None
) -> DataFrame:
    """
    Add multiple columns to a PySpark DataFrame efficiently.
    
    This function uses withColumns() (Spark 3.3+) for optimal performance,
    avoiding the projection bloat caused by chained withColumn() calls.
    
    Parameters:
    -----------
    df : DataFrame
        The input PySpark DataFrame
    columns_dict : Dict[str, Any]
        Dictionary where keys are new column names and values are either:
        - Column expressions (e.g., col("existing_col") * 2)
        - Literal values (will be wrapped with lit())
        - Existing column references
    data_types : Optional[Dict[str, str]]
        Optional dictionary to cast column data types. Keys are column names,
        values are type strings: 'string', 'int', 'long', 'double', 'boolean', 'date', 'timestamp'
    
    Returns:
    --------
    DataFrame
        New DataFrame with added columns
        
    Examples:
    ---------
    >>> # Example 1: Add constant value columns
    >>> df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])
    >>> new_df = add_columns(
    ...     df,
    ...     {
    ...         "status": "active",
    ...         "score": 100,
    ...         "is_verified": True
    ...     }
    ... )
    
    >>> # Example 2: Add derived columns
    >>> df = spark.createDataFrame([(1, 100), (2, 200)], ["id", "amount"])
    >>> new_df = add_columns(
    ...     df,
    ...     {
    ...         "amount_doubled": col("amount") * 2,
    ...         "amount_squared": col("amount") ** 2,
    ...         "category": "standard"
    ...     }
    ... )
    
    >>> # Example 3: Add columns with specific data types
    >>> df = spark.createDataFrame([(1, "100.5"), (2, "200.5")], ["id", "value"])
    >>> new_df = add_columns(
    ...     df,
    ...     {
    ...         "value_numeric": col("value"),
    ...         "id_string": col("id"),
    ...         "constant": 1
    ...     },
    ...     data_types={
    ...         "value_numeric": "double",
    ...         "id_string": "string",
    ...         "constant": "long"
    ...     }
    ... )
    """
    # Type mapping
    type_map = {
        'string': StringType(),
        'int': IntegerType(),
        'integer': IntegerType(),
        'long': LongType(),
        'double': DoubleType(),
        'float': DoubleType(),
        'boolean': BooleanType(),
        'bool': BooleanType(),
        'date': DateType(),
        'timestamp': TimestampType()
    }
    
    # Prepare columns dictionary
    cols_to_add = {}
    
    for col_name, col_value in columns_dict.items():
        # Check if value is already a Column type
        if hasattr(col_value, '_jc'):  # Column objects have _jc attribute
            cols_to_add[col_name] = col_value
        else:
            # Wrap literal values with lit()
            cols_to_add[col_name] = lit(col_value)
        
        # Apply data type casting if specified
        if data_types and col_name in data_types:
            dtype = data_types[col_name].lower()
            if dtype in type_map:
                cols_to_add[col_name] = cols_to_add[col_name].cast(type_map[dtype])
            else:
                raise ValueError(f"Unsupported data type: {dtype}. Supported types: {list(type_map.keys())}")
    
    # Use withColumns() for optimal performance (Spark 3.3+)
    return df.withColumns(cols_to_add)
```

## **Usage Examples**

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, concat_ws, current_timestamp

spark = SparkSession.builder.appName("AddColumns").getOrCreate()

# Create sample data
df = spark.createDataFrame([
    (1, "Alice", 25, 50000),
    (2, "Bob", 30, 60000),
    (3, "Charlie", 35, 75000)
], ["id", "name", "age", "salary"])

# Example 1: Add multiple constant columns
df1 = add_columns(
    df,
    {
        "department": "Engineering",
        "country": "USA",
        "is_active": True,
        "hire_year": 2020
    }
)
df1.show()

# Example 2: Add derived columns
df2 = add_columns(
    df,
    {
        "salary_monthly": col("salary") / 12,
        "age_category": when(col("age") < 30, "Young")
                        .when(col("age") < 40, "Mid")
                        .otherwise("Senior"),
        "bonus": col("salary") * 0.1
    },
    data_types={
        "salary_monthly": "double",
        "bonus": "double"
    }
)
df2.show()

# Example 3: Complex transformations
df3 = add_columns(
    df,
    {
        "full_id": concat_ws("-", lit("EMP"), col("id").cast("string")),
        "salary_band": when(col("salary") < 55000, "Band-1")
                       .when(col("salary") < 70000, "Band-2")
                       .otherwise("Band-3"),
        "years_to_retirement": lit(65) - col("age"),
        "timestamp_added": current_timestamp()
    }
)
df3.show(truncate=False)
```

## **Key Advantages**

1. **High Performance**: Uses `withColumns()` which adds only ONE projection node regardless of column count
2. **Type Safety**: Built-in data type casting with validation
3. **Flexibility**: Handles both literal values and complex Column expressions
4. **Simplicity**: Single function call instead of multiple chained operations
5. **Memory Efficient**: Avoids creating intermediate DataFrames for each column

## **Performance Comparison**

```python
# ❌ AVOID: Chained withColumn() - Creates N projection nodes
df_bad = df.withColumn("col1", lit(1))\
           .withColumn("col2", lit(2))\
           .withColumn("col3", lit(3))  # 3 projection nodes!

# ✅ RECOMMENDED: Using withColumns() - Creates 1 projection node
df_good = add_columns(df, {
    "col1": 1,
    "col2": 2,
    "col3": 3
})  # Only 1 projection node!
```

This approach follows PySpark's official best practices introduced in Spark 3.3