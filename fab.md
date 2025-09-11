# Microsoft Fabric Workspace Cleanup & Optimization Runbook

## Executive Summary
This runbook provides a phased approach to clean up and optimize a Microsoft Fabric Workspace running on F64 SKU, transitioning ownership from individual users to Service Principal, optimizing data connections, and improving Spark performance.

## Prerequisites

### 1. Service Principal Setup
- Service Principal with Admin permissions on the workspace
- Client ID, Client Secret, and Tenant ID stored securely
- Azure Key Vault (optional but recommended) for secret management

### 2. Fabric Tenant Settings
Enable the following in Fabric Admin Portal:
- "Service principals can use Fabric APIs"
- "Allow service principals to use Power BI APIs"
- "Service principals can access OneLake"

### 3. Required Python Packages
```python
# Install in your notebook or environment
!pip install semantic-link-sempy>=0.12.0
!pip install semantic-link
!pip install pandas>=2.0.0
!pip install azure-identity
!pip install azure-storage-file-datalake
!pip install deltalake
```

### 4. F64 SKU Specifications
- **Capacity Units**: 64 CUs
- **Spark vCores**: 128 base (384 with 3x burst factor)
- **Maximum concurrent jobs**: Depends on pool configuration
- **Recommended node sizes**: Medium (8 vCores) to Large (16 vCores)

---

## Phase 1: Discovery & Inventory Generation

### Step 1.1: Initialize Authentication and Setup

```python
# notebook: 01_initialize_setup.py
# Description: Initialize authentication and workspace connection

import sempy
import sempy.fabric as fabric
import pandas as pd
import json
from datetime import datetime
import notebookutils
from azure.identity import ClientSecretCredential
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get current workspace ID
workspace_id = notebookutils.runtime.context.get("currentWorkspaceId")
workspace_name = notebookutils.runtime.context.get("currentWorkspaceName")

# Service Principal Authentication (if using Key Vault)
key_vault = "https://yourvault.vault.azure.net/"  # Update with your vault
tenant_id = notebookutils.credentials.getSecret(key_vault, "tenantid")
client_id = notebookutils.credentials.getSecret(key_vault, "pbi-sp-applicationid")
client_secret = notebookutils.credentials.getSecret(key_vault, "powerbi-sp-clientsecret")

# Alternative: Direct configuration (less secure)
# tenant_id = "your-tenant-id"
# client_id = "your-client-id"
# client_secret = "your-client-secret"

# Create credential object
credential = ClientSecretCredential(
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret
)

logger.info(f"Initialized workspace: {workspace_name} ({workspace_id})")
logger.info(f"Service Principal: {client_id}")

# Store configuration for reuse
config = {
    "workspace_id": workspace_id,
    "workspace_name": workspace_name,
    "tenant_id": tenant_id,
    "client_id": client_id,
    "timestamp": datetime.now().isoformat()
}

# Save configuration
with open("/lakehouse/default/Files/workspace_config.json", "w") as f:
    json.dump(config, f, indent=2)
```

### Step 1.2: Generate Comprehensive Inventory

```python
# notebook: 02_generate_inventory.py
# Description: Create comprehensive inventory of all workspace artifacts

import sempy.fabric as fabric
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_workspace_items(workspace_id):
    """Get all items in workspace with details"""
    try:
        # Get all workspace items
        items = fabric.list_items(workspace=workspace_id)
        return items
    except Exception as e:
        logger.error(f"Error getting workspace items: {e}")
        return pd.DataFrame()

def get_datasets_details(workspace_id):
    """Get detailed information about datasets"""
    try:
        datasets = fabric.list_datasets(workspace=workspace_id, mode='rest')
        dataset_details = []
        
        for _, dataset in datasets.iterrows():
            dataset_id = dataset['Id']
            dataset_name = dataset['Name']
            
            try:
                # Get datasources for each dataset
                datasources = fabric.list_datasources(
                    dataset=dataset_id,
                    workspace=workspace_id
                )
                
                # Get relationships
                relationships = fabric.list_relationships(
                    dataset=dataset_id,
                    workspace=workspace_id,
                    extended=True
                )
                
                # Get tables
                tables = fabric.list_tables(
                    dataset=dataset_id,
                    workspace=workspace_id
                )
                
                dataset_details.append({
                    'dataset_id': dataset_id,
                    'dataset_name': dataset_name,
                    'owner': dataset.get('Owner', 'Unknown'),
                    'created_date': dataset.get('CreatedDate'),
                    'modified_date': dataset.get('ModifiedDate'),
                    'size_bytes': dataset.get('SizeInBytes', 0),
                    'datasource_count': len(datasources),
                    'table_count': len(tables),
                    'relationship_count': len(relationships),
                    'datasources': datasources.to_dict('records') if not datasources.empty else [],
                    'tables': tables['Name'].tolist() if not tables.empty else []
                })
            except Exception as e:
                logger.warning(f"Could not get details for dataset {dataset_name}: {e}")
                
        return pd.DataFrame(dataset_details)
    except Exception as e:
        logger.error(f"Error getting dataset details: {e}")
        return pd.DataFrame()

def get_notebooks_details(workspace_id):
    """Get notebook details including dependencies"""
    try:
        notebooks = fabric.list_items(workspace=workspace_id, type='Notebook')
        notebook_details = []
        
        for _, notebook in notebooks.iterrows():
            notebook_details.append({
                'notebook_id': notebook['Id'],
                'notebook_name': notebook['Name'],
                'owner': notebook.get('Owner', 'Unknown'),
                'created_date': notebook.get('CreatedDate'),
                'modified_date': notebook.get('ModifiedDate'),
                'type': 'Notebook'
            })
            
        return pd.DataFrame(notebook_details)
    except Exception as e:
        logger.error(f"Error getting notebook details: {e}")
        return pd.DataFrame()

def get_lakehouse_details(workspace_id):
    """Get lakehouse details"""
    try:
        lakehouses = fabric.list_items(workspace=workspace_id, type='Lakehouse')
        lakehouse_details = []
        
        for _, lakehouse in lakehouses.iterrows():
            lakehouse_details.append({
                'lakehouse_id': lakehouse['Id'],
                'lakehouse_name': lakehouse['Name'],
                'owner': lakehouse.get('Owner', 'Unknown'),
                'created_date': lakehouse.get('CreatedDate'),
                'modified_date': lakehouse.get('ModifiedDate'),
                'sql_endpoint_id': lakehouse.get('SqlEndpointProperties', {}).get('Id'),
                'type': 'Lakehouse'
            })
            
        return pd.DataFrame(lakehouse_details)
    except Exception as e:
        logger.error(f"Error getting lakehouse details: {e}")
        return pd.DataFrame()

def get_data_pipeline_details(workspace_id):
    """Get data pipeline details"""
    try:
        pipelines = fabric.list_items(workspace=workspace_id, type='DataPipeline')
        return pipelines
    except Exception as e:
        logger.error(f"Error getting pipeline details: {e}")
        return pd.DataFrame()

def get_spark_job_definitions(workspace_id):
    """Get Spark job definition details"""
    try:
        spark_jobs = fabric.list_items(workspace=workspace_id, type='SparkJobDefinition')
        return spark_jobs
    except Exception as e:
        logger.error(f"Error getting Spark job details: {e}")
        return pd.DataFrame()

def generate_inventory_report(workspace_id):
    """Generate comprehensive inventory report"""
    logger.info("Starting inventory generation...")
    
    # Collect all artifact types
    all_items = get_workspace_items(workspace_id)
    datasets = get_datasets_details(workspace_id)
    notebooks = get_notebooks_details(workspace_id)
    lakehouses = get_lakehouse_details(workspace_id)
    pipelines = get_data_pipeline_details(workspace_id)
    spark_jobs = get_spark_job_definitions(workspace_id)
    
    # Create summary report
    summary = {
        'workspace_id': workspace_id,
        'scan_timestamp': datetime.now().isoformat(),
        'total_items': len(all_items),
        'datasets': len(datasets),
        'notebooks': len(notebooks),
        'lakehouses': len(lakehouses),
        'pipelines': len(pipelines),
        'spark_jobs': len(spark_jobs)
    }
    
    # Combine all artifacts
    all_artifacts = pd.concat([
        datasets.assign(artifact_type='Dataset') if not datasets.empty else pd.DataFrame(),
        notebooks.assign(artifact_type='Notebook') if not notebooks.empty else pd.DataFrame(),
        lakehouses.assign(artifact_type='Lakehouse') if not lakehouses.empty else pd.DataFrame(),
        pipelines.assign(artifact_type='DataPipeline') if not pipelines.empty else pd.DataFrame(),
        spark_jobs.assign(artifact_type='SparkJobDefinition') if not spark_jobs.empty else pd.DataFrame()
    ], ignore_index=True)
    
    # Fill missing columns
    required_columns = ['artifact_type', 'owner', 'created_date', 'modified_date']
    for col in required_columns:
        if col not in all_artifacts.columns:
            all_artifacts[col] = None
    
    # Add ownership analysis
    ownership_summary = all_artifacts.groupby(['artifact_type', 'owner']).size().reset_index(name='count')
    
    # Save reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save detailed inventory
    inventory_path = f"/lakehouse/default/Files/inventory_{timestamp}.csv"
    all_artifacts.to_csv(inventory_path, index=False)
    logger.info(f"Inventory saved to: {inventory_path}")
    
    # Save ownership summary
    ownership_path = f"/lakehouse/default/Files/ownership_summary_{timestamp}.csv"
    ownership_summary.to_csv(ownership_path, index=False)
    logger.info(f"Ownership summary saved to: {ownership_path}")
    
    # Save summary JSON
    summary_path = f"/lakehouse/default/Files/inventory_summary_{timestamp}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to: {summary_path}")
    
    return all_artifacts, ownership_summary, summary

# Execute inventory generation
all_artifacts, ownership_summary, summary = generate_inventory_report(workspace_id)

# Display results
print(f"\n=== Inventory Summary ===")
print(f"Total artifacts: {summary['total_items']}")
print(f"\n=== Ownership Distribution ===")
print(ownership_summary.to_string())
```

### Step 1.3: Analyze Dependencies and Relationships

```python
# notebook: 03_analyze_dependencies.py
# Description: Analyze dependencies between artifacts

import networkx as nx
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)

def analyze_dataset_dependencies(workspace_id):
    """Analyze dependencies between datasets and other artifacts"""
    dependencies = []
    
    try:
        datasets = fabric.list_datasets(workspace=workspace_id, mode='rest')
        
        for _, dataset in datasets.iterrows():
            dataset_id = dataset['Id']
            dataset_name = dataset['Name']
            
            # Get dependent reports
            reports = fabric.list_items(workspace=workspace_id, type='Report')
            for _, report in reports.iterrows():
                if report.get('DatasetId') == dataset_id:
                    dependencies.append({
                        'source_type': 'Dataset',
                        'source_id': dataset_id,
                        'source_name': dataset_name,
                        'target_type': 'Report',
                        'target_id': report['Id'],
                        'target_name': report['Name'],
                        'dependency_type': 'DataSource'
                    })
                    
            # Get dataflows dependencies
            try:
                datasources = fabric.list_datasources(dataset=dataset_id, workspace=workspace_id)
                for _, ds in datasources.iterrows():
                    if ds.get('DatasourceType') == 'AnalysisServices':
                        dependencies.append({
                            'source_type': 'Dataset',
                            'source_id': dataset_id,
                            'source_name': dataset_name,
                            'target_type': 'Datasource',
                            'target_id': ds.get('DatasourceId'),
                            'target_name': ds.get('Name'),
                            'dependency_type': 'DataConnection'
                        })
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
    
    return pd.DataFrame(dependencies)

def create_dependency_graph(dependencies_df):
    """Create a dependency graph for visualization"""
    G = nx.DiGraph()
    
    if not dependencies_df.empty:
        for _, row in dependencies_df.iterrows():
            G.add_edge(
                row['source_name'],
                row['target_name'],
                dependency_type=row['dependency_type']
            )
    
    # Calculate metrics
    metrics = {
        'total_nodes': G.number_of_nodes(),
        'total_edges': G.number_of_edges(),
        'isolated_nodes': len(list(nx.isolates(G))),
        'strongly_connected_components': nx.number_strongly_connected_components(G) if G.number_of_nodes() > 0 else 0
    }
    
    return G, metrics

# Analyze dependencies
dependencies_df = analyze_dataset_dependencies(workspace_id)
graph, metrics = create_dependency_graph(dependencies_df)

# Save dependency analysis
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
dependencies_path = f"/lakehouse/default/Files/dependencies_{timestamp}.csv"
dependencies_df.to_csv(dependencies_path, index=False)

print(f"\n=== Dependency Analysis ===")
print(f"Total dependencies found: {len(dependencies_df)}")
print(f"Graph metrics: {metrics}")
```

---

## Phase 2: Service Principal Migration

### Step 2.1: Prepare Service Principal Configuration

```python
# notebook: 04_prepare_spn_migration.py
# Description: Prepare for Service Principal migration

import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_bearer_token(tenant_id, client_id, client_secret):
    """Get bearer token for Service Principal"""
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://api.fabric.microsoft.com/.default"
    }
    
    response = requests.post(url, headers=headers, data=body)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get token: {response.text}")

def verify_spn_permissions(workspace_id, bearer_token):
    """Verify Service Principal has required permissions"""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        logger.info("Service Principal has access to workspace")
        return True
    else:
        logger.error(f"Service Principal access check failed: {response.text}")
        return False

# Get bearer token
bearer_token = get_bearer_token(tenant_id, client_id, client_secret)

# Verify permissions
if verify_spn_permissions(workspace_id, bearer_token):
    logger.info("Service Principal is ready for migration")
else:
    logger.error("Service Principal needs additional permissions")
    
# Store token for later use (expires in 1 hour)
token_info = {
    "token": bearer_token,
    "generated_at": datetime.now().isoformat(),
    "expires_in": 3600
}

with open("/lakehouse/default/Files/spn_token.json", "w") as f:
    json.dump(token_info, f)
```

### Step 2.2: Migrate Artifact Ownership

```python
# notebook: 05_migrate_ownership.py
# Description: Migrate ownership of artifacts to Service Principal

import requests
import pandas as pd
import time
import logging

logger = logging.getLogger(__name__)

def create_artifact_with_spn(artifact_type, artifact_name, workspace_id, bearer_token):
    """Create new artifact owned by Service Principal"""
    
    endpoint_map = {
        "Lakehouse": "lakehouses",
        "Warehouse": "warehouses",
        "KQLDatabase": "kqldatabases",
        "Notebook": "notebooks",
        "SparkJobDefinition": "sparkJobDefinitions"
    }
    
    if artifact_type not in endpoint_map:
        logger.warning(f"Artifact type {artifact_type} not supported for SPN creation")
        return None
    
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/{endpoint_map[artifact_type]}"
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    body = {
        "displayName": f"{artifact_name}_SPN",
        "description": f"Migrated to SPN ownership on {datetime.now().isoformat()}"
    }
    
    # Special handling for warehouses
    if artifact_type == "Warehouse":
        body["type"] = "Warehouse"
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code in [200, 201, 202]:
        logger.info(f"Created {artifact_type}: {artifact_name}_SPN")
        return response.json()
    else:
        logger.error(f"Failed to create {artifact_type}: {response.text}")
        return None

def migrate_notebooks_to_spn(workspace_id, bearer_token, notebooks_df):
    """Migrate notebooks to Service Principal ownership"""
    migration_results = []
    
    for _, notebook in notebooks_df.iterrows():
        if notebook['owner'] != client_id:  # Not already owned by SPN
            logger.info(f"Migrating notebook: {notebook['notebook_name']}")
            
            # For notebooks, we need to export content and recreate
            # This is a simplified version - in production, you'd export/import content
            result = create_artifact_with_spn(
                "Notebook",
                notebook['notebook_name'],
                workspace_id,
                bearer_token
            )
            
            migration_results.append({
                'artifact_type': 'Notebook',
                'original_name': notebook['notebook_name'],
                'new_name': f"{notebook['notebook_name']}_SPN",
                'status': 'success' if result else 'failed',
                'timestamp': datetime.now().isoformat()
            })
            
            # Rate limiting
            time.sleep(1)
    
    return pd.DataFrame(migration_results)

def migrate_warehouses_to_spn(workspace_id, bearer_token):
    """Create new warehouses owned by Service Principal"""
    
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/warehouses"
    
    headers = {
        "Authorization": f"Bearer {