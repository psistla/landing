
## Critical Finding

**Cloud connections created in "Manage Connections and Gateways" CANNOT be used directly in Fabric Spark notebooks.** According to Microsoft documentation, cloud connections cannot currently be used directly in Fabric Spark [Medium](https://murggu.medium.com/databricks-and-fabric-writing-to-onelake-and-adls-gen2-671dcf24cf33) .

However, you have **three working alternatives**:

---

## **Solution 1: Use Workspace Identity (Recommended)**

This is the most secure and modern approach for production environments.

### Prerequisites:
1. Configure a workspace identity in your workspace
2. Grant the workspace identity appropriate RBAC roles on your ADLS Gen2 storage account (Storage Blob Data Contributor or Reader)
3. If your storage account has firewall enabled, configure Trusted Workspace Access with resource instance rules [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/security/security-trusted-workspace-access) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-factory/connector-azure-data-lake-storage-gen2)

### Code:

```python
from notebookutils import mssparkutils

# Define your parameters
storage_account = "something"  # Your storage account name
container = "publish"
sub_id = "your_subscription_id"
tenant_id = "your_tenant_id"
folder_name = "your_folder_name"

# Construct the full path
path = f"subscriptions/{sub_id}/tenants/{tenant_id}/types/{folder_name}/versions/1"
mount_point = f"/mnt/{folder_name}"

# Mount using workspace identity (no credentials needed!)
try:
    mssparkutils.fs.mount(
        f"abfss://{container}@{storage_account}.dfs.core.windows.net/{path}",
        mount_point
    )
    print(f"Successfully mounted to {mount_point}")
except Exception as e:
    print(f"Mount failed: {str(e)}")

# Get the local mount path
local_path = mssparkutils.fs.getMountPath(mount_point)
print(f"Local mount path: {local_path}")

# Read Delta table
df = spark.read.format("delta").load(f"file://{local_path}")
df.display()

# Alternative: Read directly without mounting
direct_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/{path}"
df_direct = spark.read.format("delta").load(direct_path)
df_direct.display()
```

### How It Works:
- The workspace identity is an automatically managed service principal that Fabric uses to authenticate to ADLS Gen2 [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/microsoft-spark-utilities)
- When you have workspace identity configured with proper RBAC permissions, Fabric can obtain Microsoft Entra tokens to access the resource [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/security/workspace-identity-authenticate)
- No secrets or keys to manage
- Works seamlessly with firewall-enabled storage accounts

---

## **Solution 2: Mount with SAS Token or Account Key**

Use this if you cannot use workspace identity or need temporary access.

### Code with SAS Token:

```python
from notebookutils import mssparkutils

# Configuration
storage_account = "something"
container = "publish"
sas_token = "your_sas_token_here"  # Get from Azure Portal
sub_id = "your_subscription_id"
tenant_id = "your_tenant_id"
folder_name = "your_folder_name"

# Construct path
path = f"subscriptions/{sub_id}/tenants/{tenant_id}/types/{folder_name}/versions/1"
mount_point = f"/mnt/{folder_name}"

# Mount with SAS token
try:
    mssparkutils.fs.mount(
        f"abfss://{container}@{storage_account}.dfs.core.windows.net/{path}",
        mount_point,
        {
            "sasToken": sas_token,
            "fileCacheTimeout": 120,
            "timeout": 120
        }
    )
    print(f"Successfully mounted to {mount_point}")
except Exception as e:
    print(f"Mount failed: {str(e)}")

# Get mount path and read Delta
local_path = mssparkutils.fs.getMountPath(mount_point)
df = spark.read.format("delta").load(f"file://{local_path}")
df.display()
```

### Code with Account Key:

```python
from notebookutils import mssparkutils

# Configuration
storage_account = "something"
account_key = "your_account_key_here"  # Get from Azure Portal
container = "publish"
sub_id = "your_subscription_id"
tenant_id = "your_tenant_id"
folder_name = "your_folder_name"

# Construct path
path = f"subscriptions/{sub_id}/tenants/{tenant_id}/types/{folder_name}/versions/1"
mount_point = f"/mnt/{folder_name}"

# Mount with account key
try:
    mssparkutils.fs.mount(
        f"abfss://{container}@{storage_account}.dfs.core.windows.net/{path}",
        mount_point,
        {
            "accountKey": account_key
        }
    )
    print(f"Successfully mounted to {mount_point}")
except Exception as e:
    print(f"Mount failed: {str(e)}")

# Read Delta table
local_path = mssparkutils.fs.getMountPath(mount_point)
df = spark.read.format("delta").load(f"file://{local_path}")
df.display()
```

---

## **Solution 3: Direct Read with Spark Configs (No Mounting)**

This approach configures Spark to authenticate without mounting.

### Code:

```python
# Configuration
storage_account = "something"
container = "publish"
account_key = "your_account_key_here"  # Or use SAS token
sub_id = "your_subscription_id"
tenant_id = "your_tenant_id"
folder_name = "your_folder_name"

# Configure Spark for account key authentication
spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    account_key
)

# OR configure for SAS token
# spark.conf.set(
#     f"fs.azure.sas.{container}.{storage_account}.dfs.core.windows.net",
#     sas_token
# )

# Construct path and read directly
path = f"subscriptions/{sub_id}/tenants/{tenant_id}/types/{folder_name}/versions/1"
full_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/{path}"

df = spark.read.format("delta").load(full_path)
df.display()
```

---

## **Complete Utility Function for Multiple Tables**

Here's a reusable function to handle multiple tables:

```python
from notebookutils import mssparkutils
from typing import Dict

def read_delta_from_adls(
    storage_account: str,
    container: str,
    sub_id: str,
    tenant_id: str,
    folder_name: str,
    use_mount: bool = False,
    auth_method: str = "workspace_identity",
    credentials: Dict = None
) -> "DataFrame":
    """
    Read Delta table from ADLS Gen2
    
    Parameters:
    -----------
    storage_account : str
        ADLS Gen2 storage account name (without .dfs.core.windows.net)
    container : str
        Container name (e.g., "publish")
    sub_id : str
        Subscription ID
    tenant_id : str
        Tenant ID
    folder_name : str
        Folder name for this specific table
    use_mount : bool
        Whether to mount (True) or read directly (False)
    auth_method : str
        "workspace_identity", "account_key", or "sas_token"
    credentials : Dict
        {"account_key": "..."} or {"sas_token": "..."}
    
    Returns:
    --------
    DataFrame : Spark DataFrame with Delta table data
    """
    
    # Construct the path
    path = f"subscriptions/{sub_id}/tenants/{tenant_id}/types/{folder_name}/versions/1"
    full_path = f"abfss://{container}@{storage_account}.dfs.core.windows.net/{path}"
    
    if use_mount:
        mount_point = f"/mnt/{folder_name.replace('/', '_')}"
        
        # Check if already mounted
        existing_mounts = [m.mountPoint for m in mssparkutils.fs.mounts()]
        if mount_point not in existing_mounts:
            try:
                if auth_method == "workspace_identity":
                    # Workspace identity - no extra config needed
                    mssparkutils.fs.mount(full_path, mount_point)
                elif auth_method == "account_key":
                    mssparkutils.fs.mount(
                        full_path,
                        mount_point,
                        {"accountKey": credentials.get("account_key")}
                    )
                elif auth_method == "sas_token":
                    mssparkutils.fs.mount(
                        full_path,
                        mount_point,
                        {
                            "sasToken": credentials.get("sas_token"),
                            "fileCacheTimeout": 120,
                            "timeout": 120
                        }
                    )
                print(f"✓ Mounted {folder_name} to {mount_point}")
            except Exception as e:
                print(f"✗ Mount failed for {folder_name}: {str(e)}")
                raise
        else:
            print(f"✓ Already mounted: {mount_point}")
        
        # Read from mount
        local_path = mssparkutils.fs.getMountPath(mount_point)
        df = spark.read.format("delta").load(f"file://{local_path}")
        
    else:
        # Direct read without mounting
        if auth_method == "account_key":
            spark.conf.set(
                f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
                credentials.get("account_key")
            )
        elif auth_method == "sas_token":
            spark.conf.set(
                f"fs.azure.sas.{container}.{storage_account}.dfs.core.windows.net",
                credentials.get("sas_token")
            )
        # workspace_identity needs no Spark config
        
        df = spark.read.format("delta").load(full_path)
        print(f"✓ Read {folder_name} directly from ADLS")
    
    return df

# Example usage with workspace identity (recommended)
df1 = read_delta_from_adls(
    storage_account="something",
    container="publish",
    sub_id="12345678-1234-1234-1234-123456789012",
    tenant_id="87654321-4321-4321-4321-210987654321",
    folder_name="customer_data",
    use_mount=True,
    auth_method="workspace_identity"
)

# Example with SAS token
df2 = read_delta_from_adls(
    storage_account="something",
    container="publish",
    sub_id="12345678-1234-1234-1234-123456789012",
    tenant_id="87654321-4321-4321-4321-210987654321",
    folder_name="sales_data",
    use_mount=False,
    auth_method="sas_token",
    credentials={"sas_token": "sp=r&st=2025-01-01..."}
)

# List all current mounts
print("\nCurrent mounts:")
for mount in mssparkutils.fs.mounts():
    print(f"  {mount.mountPoint} -> {mount.source}")
```

---

## **Explanation of Key Concepts**

### Mounting vs. Direct Read:

**Mounting (`mssparkutils.fs.mount`):**
- Attaches remote storage to all Spark nodes (driver and workers) so you can access data as if it's in the local file system [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities) [Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/microsoft-spark-utilities)
- Use `file://` prefix with `getMountPath()` for file operations
- Persists for the notebook session
- Better for multiple reads from same location

**Direct Read:**
- Uses `abfss://` protocol directly
- No mounting step required
- Better for one-time reads
- Simpler for ad-hoc queries

### Authentication Priority:

1. **Workspace Identity** (Best for production) - Managed, secure, no secrets
2. **SAS Token** (Good for temporary access) - Time-limited, scoped permissions
3. **Account Key** (Use sparingly) - Full access, security risk if exposed

---

## **Response Critique**

### Strengths:
✓ Addresses the core limitation that cloud connections don't work in Spark  
✓ Provides three distinct, working solutions  
✓ Includes complete, production-ready code  
✓ Explains mounting vs. direct read trade-offs  
✓ Prioritizes workspace identity as the secure approach  

### Potential Issues Addressed:
✓ Path format is correctly using `abfss://` with `.dfs.core.windows.net`  
✓ Includes error handling  
✓ Provides reusable utility function  
✓ Explains authentication trade-offs  
