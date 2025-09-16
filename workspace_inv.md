# Microsoft Fabric Workspace Inventory Generator - Complete Setup Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Authentication Setup](#authentication-setup)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

---

## 🎯 Overview

This solution provides a comprehensive inventory generator for Microsoft Fabric workspaces using semantic-link and semantic-link-labs libraries. It collects detailed metadata about all artifacts including:

- **Workspace Information**: ID, name, capacity, creation/modification dates
- **Semantic Models**: Tables, measures, relationships, columns, RLS settings
- **Reports**: Connected datasets, pages, visuals, last modified info
- **Lakehouses**: Storage details, SQL endpoints
- **Notebooks**: Dependencies, last run status
- **Data Pipelines**: Activities, connections
- **Dataflows**: Data sources, transformations

### Key Features
- ✅ **No secrets required** - Uses certificate-based auth or Managed Identity
- ✅ **Comprehensive metadata** collection
- ✅ **Delta table storage** for historical tracking
- ✅ **Tenant-wide policy compliant** (no secrets)
- ✅ **F32 SKU optimized**

---

## 📦 Prerequisites

### 1. **Microsoft Fabric Environment**
- Microsoft Fabric workspace with F32 SKU capacity
- Workspace with appropriate permissions (Admin/Member/Contributor)
- Lakehouse for storing inventory data

### 2. **Required Permissions**

#### For Service Principal:
- **Azure AD Permissions**:
  - Application.Read.All (for reading app registrations)
  - Directory.Read.All (for reading directory objects)
  
- **Fabric Permissions**:
  - Workspace access (Admin/Member/Contributor role)
  - Power BI Service Principal API enabled in Admin Portal
  - Fabric REST APIs enabled

#### For Managed Identity:
- Workspace Identity created and configured
- Permissions granted to access workspace artifacts

### 3. **Admin Portal Settings**
Navigate to Admin Portal → Tenant Settings and enable:
- ✅ Service principals can use Power BI APIs
- ✅ Service principals can access read-only admin APIs
- ✅ Allow service principals to use Fabric APIs
- ✅ Workspace Identity support

---

## 🔐 Authentication Setup

### Option 1: Workspace/Managed Identity (Recommended)

#### Step 1: Create Workspace Identity
```powershell
# In Fabric Portal
1. Go to your workspace
2. Click Settings → Workspace settings
3. Select "Identity" tab
4. Click "Create identity"
5. Note the Object ID created
```

#### Step 2: Grant Permissions
```powershell
# Azure Portal - Assign roles to the Managed Identity
1. Navigate to Azure Portal
2. Go to your resource (Storage Account, Key Vault, etc.)
3. Access Control (IAM) → Add role assignment
4. Select appropriate role (e.g., "Storage Blob Data Reader")
5. Assign to → Managed Identity → Select your workspace identity
```

#### Step 3: Configure in Notebook
```python
# No configuration needed - automatically uses workspace identity
# The notebook will use the workspace's managed identity by default
```

### Option 2: Service Principal with Certificate (No Secrets)

#### Step 1: Create Service Principal
```powershell
# Azure CLI commands
# 1. Create Service Principal
az ad sp create-for-rbac --name "fabric-inventory-spn" --skip-assignment

# 2. Note the output:
# {
#   "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # CLIENT_ID
#   "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # TENANT_ID
# }
```

#### Step 2: Generate and Upload Certificate
```bash
# Generate self-signed certificate (Linux/Mac/WSL)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=fabric-inventory-cert"

# Combine into PFX (optional)
openssl pkcs12 -export -out certificate.pfx -inkey key.pem -in cert.pem

# Upload certificate to Azure AD App
az ad app credential reset --id <APP_ID> --cert @cert.pem --append
```

#### Step 3: Grant Fabric Permissions
```powershell
# In Fabric Portal
1. Go to your workspace
2. Click "Manage access"
3. Add people or groups
4. Search for your Service Principal by name or App ID
5. Assign role (Admin/Member/Contributor)
6. Click "Add"
```

#### Step 4: Configure API Permissions
```powershell
# Azure Portal
1. Azure AD → App registrations → Your App
2. API permissions → Add permission
3. Select "Power BI Service"
4. Add permissions:
   - Workspace.Read.All
   - Dataset.Read.All
   - Report.Read.All
   - Dataflow.Read.All
5. Grant admin consent (if required)
```

---

## 📝 Step-by-Step Implementation

### Step 1: Create a New Notebook in Fabric

1. **Navigate to your Fabric workspace**
2. **Click "New" → "Notebook"**
3. **Name it**: `Fabric_Inventory_Generator`
4. **Attach to Lakehouse**: Select your lakehouse from the explorer

### Step 2: Install Required Libraries

In the first cell of your notebook:
```python
# Install required packages
%pip install -U semantic-link semantic-link-labs azure-identity
```

### Step 3: Configure Authentication

**For Managed Identity:**
```python
# Set environment variables (optional - for user-assigned identity)
import os
os.environ['AZURE_CLIENT_ID'] = 'your-managed-identity-client-id'  # Optional
```

**For Service Principal:**
```python
# Set environment variables
import os
os.environ['TENANT_ID'] = 'your-tenant-id'
os.environ['CLIENT_ID'] = 'your-service-principal-id'
os.environ['CERT_PATH'] = '/lakehouse/default/Files/certificate.pem'
```

### Step 4: Upload Certificate (Service Principal only)

1. In the notebook, navigate to the Files section
2. Upload your certificate file (`.pem` or `.pfx`)
3. Note the path: `/lakehouse/default/Files/certificate.pem`

### Step 5: Run the Inventory Generator

Copy the main code from the Python artifact and run:

```python
# Run inventory collection
inventory = run_fabric_inventory(
    workspace_name="YOUR_WORKSPACE_NAME",
    auth_method="managed_identity",  # or "service_principal"
    save_to_delta=True
)
```

### Step 6: Verify Results

```python
# Check the collected data
print(f"Total items collected: {len(inventory['all_items'])}")
print(f"Semantic models: {len(inventory['semantic_models'])}")
print(f"Reports: {len(inventory['reports'])}")

# Display sample data
display(inventory['semantic_models'].head())
```

### Step 7: Query Delta Tables

```sql
-- In a SQL cell, query the saved inventory
%%sql
SELECT * FROM fabric_inventory_semantic_models
WHERE scan_timestamp = (SELECT MAX(scan_timestamp) FROM fabric_inventory_semantic_models)
LIMIT 10;
```

---

## 💡 Usage Examples

### Example 1: Basic Inventory with Managed Identity
```python
# Simplest usage - uses workspace's managed identity
inventory = run_fabric_inventory(
    workspace_name="Analytics_Workspace",
    auth_method="managed_identity",
    save_to_delta=True
)
```

### Example 2: Service Principal with Certificate
```python
# Using Service Principal (no secrets)
inventory = run_fabric_inventory(
    workspace_name="Analytics_Workspace",
    auth_method="service_principal",
    tenant_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    client_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    cert_path="/lakehouse/default/Files/fabric-cert.pem",
    save_to_delta=True
)
```

### Example 3: Filter and Analyze Results
```python
# Find all Direct Lake models
direct_lake_models = inventory['semantic_models'][
    inventory['semantic_models']['content_provider_type'] == 'DirectLake'
]

# Find reports without RLS
unsafe_models = inventory['semantic_models'][
    inventory['semantic_models']['is_effective_identity_required'] == False
]

# Find large models (>10 tables)
large_models = inventory['semantic_models'][
    inventory['semantic_models']['table_count'] > 10
]
```

### Example 4: Create Monitoring Report
```python
# Generate summary statistics
summary = {
    'Total Workspaces': 1,
    'Total Items': len(inventory['all_items']),
    'Semantic Models': len(inventory['semantic_models']),
    'Reports': len(inventory['reports']),
    'Lakehouses': len(inventory['lakehouses']),
    'Notebooks': len(inventory['notebooks']),
    'Pipelines': len(inventory['data_pipelines']),
    'Last Scan': inventory['workspace_info']['scan_timestamp'].iloc[0]
}

# Convert to DataFrame for visualization
summary_df = pd.DataFrame([summary])
display(summary_df)
```

### Example 5: Schedule Automated Inventory
```python
# Create a scheduled notebook run
# In Fabric Portal:
# 1. Select your notebook
# 2. Click "Schedule"
# 3. Set frequency (e.g., daily at 2 AM)
# 4. Save schedule

# Add notification in code:
def send_completion_notification():
    print("✅ Inventory scan completed successfully")
    # Add your notification logic here (email, Teams, etc.)

# Run with notification
inventory = run_fabric_inventory(
    workspace_name="Analytics_Workspace",
    auth_method="managed_identity",
    save_to_delta=True
)
send_completion_notification()
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **Authentication Failures**

**Error**: "Failed to configure managed identity"
```python
# Solution: Verify workspace identity is created
# Go to Workspace Settings → Identity → Create Identity
```

**Error**: "Invalid certificate path"
```python
# Solution: Verify certificate upload
import os
print(os.listdir('/lakehouse/default/Files/'))
# Ensure certificate file exists
```

#### 2. **Permission Issues**

**Error**: "Access denied to workspace"
```python
# Solution: Check Service Principal permissions
# 1. Verify workspace access (Admin/Member/Contributor)
# 2. Check Admin Portal settings for API access
# 3. Ensure tenant allows Service Principals
```

#### 3. **API Limitations**

**Error**: "Rate limit exceeded"
```python
# Solution: Add retry logic
import time
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def collect_with_retry():
    return collector.generate_inventory()
```

#### 4. **Missing Data**

**Issue**: Some artifacts not appearing in inventory
```python
# Solution: Check item types and permissions
# Verify the collector includes all artifact types:
print(fabric.list_items(workspace=workspace_id)['Type'].unique())
```

---

## ✅ Best Practices

### 1. **Security Best Practices**
- ✅ Always use Managed Identity when possible
- ✅ If using Service Principal, use certificate authentication (no secrets)
- ✅ Rotate certificates annually
- ✅ Apply principle of least privilege
- ✅ Monitor access logs regularly

### 2. **Performance Optimization**
```python
# Batch API calls
def batch_collect(items, batch_size=50):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        results.extend(process_batch(batch))
    return results

# Use caching for repeated queries
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_workspace_info(workspace_id):
    return fabric.list_workspaces()
```

### 3. **Data Management**
```python
# Implement data retention
def cleanup_old_inventory(days_to_keep=90):
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    spark.sql(f"""
        DELETE FROM fabric_inventory_all_items
        WHERE scan_timestamp < '{cutoff_date.isoformat()}'
    """)
```

### 4. **Error Handling**
```python
# Comprehensive error handling
def safe_collect(collector_func, default_value=pd.DataFrame()):
    try:
        result = collector_func()
        if result is None:
            return default_value
        return result
    except Exception as e:
        print(f"Warning: {collector_func.__name__} failed: {str(e)}")
        return default_value
```

### 5. **Monitoring & Alerting**
```python
# Add monitoring metrics
def log_metrics(inventory):
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'workspace': inventory['workspace_info']['workspace_name'].iloc[0],
        'total_items': len(inventory['all_items']),
        'execution_time': time.time() - start_time,
        'errors': error_count
    }
    
    # Save metrics to monitoring table
    spark_metrics = spark.createDataFrame([metrics])
    spark_metrics.write.mode("append").saveAsTable("inventory_metrics")
```

---

## 📊 Output Schema

### Inventory Tables Created

1. **fabric_inventory_workspace_info**
   - workspace_id, workspace_name, capacity_id, state, created_date, modified_date

2. **fabric_inventory_all_items**
   - Id, DisplayName, Type, Description, LastModifiedBy, LastModifiedDateTime

3. **fabric_inventory_semantic_models**
   - model_id, model_name, table_count, measure_count, relationship_count, is_refreshable

4. **fabric_inventory_reports**
   - Id, Name, connected_dataset, WebUrl, EmbedUrl, LastModifiedDateTime

5. **fabric_inventory_lakehouses**
   - Id, DisplayName, Properties, OneLakeFilesPath, OneLakeTablesPath

6. **fabric_inventory_notebooks**
   - Id, DisplayName, LastModifiedDateTime, LastModifiedBy

7. **fabric_inventory_data_pipelines**
   - Id, DisplayName, LastModifiedDateTime, Properties

8. **fabric_inventory_dataflows**
   - Id, DisplayName, Type, LastModifiedDateTime, ConfiguredBy

---

## 🎉 Conclusion

This comprehensive inventory solution provides:
- ✅ Complete workspace visibility
- ✅ Secure, secret-free authentication
- ✅ Detailed artifact metadata
- ✅ Historical tracking via Delta tables
- ✅ Scalable and maintainable architecture

For additional support or customization needs, refer to:
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric)
- [Semantic Link Documentation](https://learn.microsoft.com/python/api/semantic-link)
- [Semantic Link Labs GitHub](https://github.com/microsoft/semantic-link-labs)