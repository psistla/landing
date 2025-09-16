"""
Microsoft Fabric Workspace Inventory Generator
==============================================
Purpose: Generate comprehensive inventory for Microsoft Fabric workspace
Author: Fabric Expert
Environment: Microsoft Fabric F32 SKU
Authentication: Service Principal or Managed Identity (no secrets)
Dependencies: semantic-link, semantic-link-labs
"""

# ============================================================================
# SECTION 1: INITIAL SETUP AND IMPORTS
# ============================================================================

# Install required packages (run once per session if not in environment)
# %pip install -U semantic-link semantic-link-labs azure-identity

# Import required libraries
import sempy.fabric as fabric
import sempy_labs as labs
from sempy_labs import ServicePrincipalTokenProvider
from sempy_labs.admin import list_workspaces, list_items
from sempy_labs.tom import connect_semantic_model
import pandas as pd
from datetime import datetime, timezone
import json
import warnings
warnings.filterwarnings('ignore')

# For authentication
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, ClientCertificateCredential
import os
from typing import Dict, List, Optional, Any
from uuid import UUID

# ============================================================================
# SECTION 2: AUTHENTICATION CONFIGURATION
# ============================================================================

class FabricAuthenticator:
    """
    Handles authentication to Microsoft Fabric using Service Principal or Managed Identity
    No secrets required - uses certificate-based auth or managed identity
    """
    
    def __init__(self, auth_method: str = "managed_identity"):
        """
        Initialize authenticator
        
        Args:
            auth_method: Either 'managed_identity' or 'service_principal'
        """
        self.auth_method = auth_method
        self.credential = None
        
    def setup_managed_identity(self, client_id: Optional[str] = None):
        """
        Setup Managed Identity authentication
        
        Args:
            client_id: Optional client ID for user-assigned managed identity
        """
        try:
            if client_id:
                # User-assigned managed identity
                self.credential = ManagedIdentityCredential(client_id=client_id)
                print(f"✓ Configured user-assigned managed identity: {client_id}")
            else:
                # System-assigned managed identity
                self.credential = ManagedIdentityCredential()
                print("✓ Configured system-assigned managed identity")
        except Exception as e:
            print(f"✗ Failed to configure managed identity: {str(e)}")
            raise
    
    def setup_service_principal_cert(self, 
                                    tenant_id: str,
                                    client_id: str,
                                    cert_path: str):
        """
        Setup Service Principal with certificate authentication (no secrets)
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Service Principal application ID
            cert_path: Path to certificate file (.pem or .pfx)
        """
        try:
            self.credential = ClientCertificateCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                certificate_path=cert_path
            )
            print(f"✓ Configured Service Principal with certificate: {client_id}")
        except Exception as e:
            print(f"✗ Failed to configure Service Principal: {str(e)}")
            raise
    
    def get_token_provider(self) -> ServicePrincipalTokenProvider:
        """
        Get token provider for semantic-link-labs
        
        Returns:
            ServicePrincipalTokenProvider instance
        """
        if not self.credential:
            raise ValueError("Authentication not configured. Run setup method first.")
        
        # Get token for Fabric API
        token = self.credential.get_token("https://api.fabric.microsoft.com/.default")
        
        # Create token provider for semantic-link-labs
        return ServicePrincipalTokenProvider.from_aad_application_key_authentication(
            tenant_id=os.environ.get("TENANT_ID", ""),
            client_id=os.environ.get("CLIENT_ID", ""),
            client_secret=""  # Empty as we use certificate
        )

# ============================================================================
# SECTION 3: INVENTORY COLLECTOR
# ============================================================================

class FabricInventoryCollector:
    """
    Collects comprehensive inventory from Microsoft Fabric workspace
    """
    
    def __init__(self, workspace_name: str, auth_provider: Optional[Any] = None):
        """
        Initialize inventory collector
        
        Args:
            workspace_name: Name of the Fabric workspace to inventory
            auth_provider: Optional authentication provider
        """
        self.workspace_name = workspace_name
        self.workspace_id = None
        self.auth_provider = auth_provider
        self.inventory_data = {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
    def resolve_workspace(self) -> str:
        """
        Resolve workspace name to ID
        
        Returns:
            Workspace ID
        """
        try:
            workspaces = fabric.list_workspaces()
            ws = workspaces[workspaces['Name'] == self.workspace_name]
            if ws.empty:
                raise ValueError(f"Workspace '{self.workspace_name}' not found")
            self.workspace_id = ws.iloc[0]['Id']
            print(f"✓ Resolved workspace: {self.workspace_name} -> {self.workspace_id}")
            return self.workspace_id
        except Exception as e:
            print(f"✗ Failed to resolve workspace: {str(e)}")
            raise
    
    def collect_workspace_info(self) -> Dict:
        """
        Collect workspace-level information
        
        Returns:
            Dictionary with workspace metadata
        """
        print("\n📊 Collecting workspace information...")
        
        try:
            # Get workspace details
            workspaces = fabric.list_workspaces()
            ws_info = workspaces[workspaces['Id'] == self.workspace_id].iloc[0]
            
            workspace_data = {
                'workspace_id': self.workspace_id,
                'workspace_name': self.workspace_name,
                'description': ws_info.get('Description', ''),
                'type': ws_info.get('Type', ''),
                'state': ws_info.get('State', ''),
                'capacity_id': ws_info.get('CapacityId', ''),
                'created_date': ws_info.get('CreatedDate', ''),
                'modified_date': ws_info.get('ModifiedDate', ''),
                'scan_timestamp': self.timestamp
            }
            
            print(f"  ✓ Workspace: {workspace_data['workspace_name']}")
            print(f"  ✓ Capacity: {workspace_data['capacity_id']}")
            
            return workspace_data
            
        except Exception as e:
            print(f"  ✗ Error collecting workspace info: {str(e)}")
            return {}
    
    def collect_all_items(self) -> pd.DataFrame:
        """
        Collect all items/artifacts in the workspace
        
        Returns:
            DataFrame with all items
        """
        print("\n📦 Collecting all workspace items...")
        
        try:
            # Get all items using fabric API
            items_df = fabric.list_items(workspace=self.workspace_id)
            
            if not items_df.empty:
                # Enhance with additional metadata
                items_df['scan_timestamp'] = self.timestamp
                items_df['workspace_name'] = self.workspace_name
                
                # Count by type
                item_counts = items_df['Type'].value_counts()
                print(f"  ✓ Found {len(items_df)} items:")
                for item_type, count in item_counts.items():
                    print(f"    • {item_type}: {count}")
            else:
                print("  ℹ No items found in workspace")
                
            return items_df
            
        except Exception as e:
            print(f"  ✗ Error collecting items: {str(e)}")
            return pd.DataFrame()
    
    def collect_semantic_models(self) -> pd.DataFrame:
        """
        Collect detailed information about semantic models (datasets)
        
        Returns:
            DataFrame with semantic model details
        """
        print("\n🔷 Collecting semantic model details...")
        
        try:
            # Get all semantic models
            datasets = fabric.list_datasets(workspace=self.workspace_id)
            
            if datasets.empty:
                print("  ℹ No semantic models found")
                return pd.DataFrame()
            
            semantic_models = []
            
            for idx, dataset in datasets.iterrows():
                try:
                    dataset_name = dataset['Dataset Name']
                    dataset_id = dataset['Dataset Id']
                    
                    print(f"  → Processing: {dataset_name}")
                    
                    model_info = {
                        'model_id': dataset_id,
                        'model_name': dataset_name,
                        'configured_by': dataset.get('Configured By', ''),
                        'created_date': dataset.get('Created Date', ''),
                        'content_provider_type': dataset.get('Content Provider Type', ''),
                        'is_refreshable': dataset.get('Is Refreshable', False),
                        'is_effective_identity_required': dataset.get('Is Effective Identity Required', False),
                        'is_effective_identity_roles_required': dataset.get('Is Effective Identity Roles Required', False),
                        'is_on_prem_gateway_required': dataset.get('Is On Prem Gateway Required', False),
                        'workspace_id': self.workspace_id,
                        'workspace_name': self.workspace_name
                    }
                    
                    # Try to get additional details
                    try:
                        # Get tables
                        tables = fabric.list_tables(
                            dataset=dataset_id,
                            workspace=self.workspace_id
                        )
                        model_info['table_count'] = len(tables) if not tables.empty else 0
                        model_info['tables'] = tables['Name'].tolist() if not tables.empty else []
                        
                        # Get measures
                        measures = fabric.list_measures(
                            dataset=dataset_id,
                            workspace=self.workspace_id
                        )
                        model_info['measure_count'] = len(measures) if not measures.empty else 0
                        
                        # Get relationships
                        relationships = fabric.list_relationships(
                            dataset=dataset_id,
                            workspace=self.workspace_id
                        )
                        model_info['relationship_count'] = len(relationships) if not relationships.empty else 0
                        
                        # Get columns count
                        columns = fabric.list_columns(
                            dataset=dataset_id,
                            workspace=self.workspace_id
                        )
                        model_info['column_count'] = len(columns) if not columns.empty else 0
                        
                    except Exception as detail_error:
                        print(f"    ⚠ Could not get full details: {str(detail_error)}")
                        model_info['table_count'] = 0
                        model_info['measure_count'] = 0
                        model_info['relationship_count'] = 0
                        model_info['column_count'] = 0
                    
                    model_info['scan_timestamp'] = self.timestamp
                    semantic_models.append(model_info)
                    
                except Exception as model_error:
                    print(f"    ✗ Error processing model {dataset_name}: {str(model_error)}")
                    continue
            
            df = pd.DataFrame(semantic_models)
            print(f"  ✓ Processed {len(semantic_models)} semantic models")
            return df
            
        except Exception as e:
            print(f"  ✗ Error collecting semantic models: {str(e)}")
            return pd.DataFrame()
    
    def collect_reports(self) -> pd.DataFrame:
        """
        Collect detailed information about Power BI reports
        
        Returns:
            DataFrame with report details
        """
        print("\n📈 Collecting report details...")
        
        try:
            reports = fabric.list_reports(workspace=self.workspace_id)
            
            if reports.empty:
                print("  ℹ No reports found")
                return pd.DataFrame()
            
            # Enhance report data
            reports['workspace_id'] = self.workspace_id
            reports['workspace_name'] = self.workspace_name
            reports['scan_timestamp'] = self.timestamp
            
            print(f"  ✓ Found {len(reports)} reports")
            
            # Try to get report connections for each report
            for idx, report in reports.iterrows():
                try:
                    report_id = report['Id']
                    # Get the dataset this report is connected to
                    if 'Dataset Id' in report:
                        reports.at[idx, 'connected_dataset'] = report['Dataset Id']
                except:
                    pass
                    
            return reports
            
        except Exception as e:
            print(f"  ✗ Error collecting reports: {str(e)}")
            return pd.DataFrame()
    
    def collect_lakehouses(self) -> pd.DataFrame:
        """
        Collect information about Lakehouses
        
        Returns:
            DataFrame with lakehouse details
        """
        print("\n🏞️ Collecting lakehouse details...")
        
        try:
            # Filter items for lakehouses
            items = fabric.list_items(workspace=self.workspace_id)
            lakehouses = items[items['Type'] == 'Lakehouse'].copy()
            
            if lakehouses.empty:
                print("  ℹ No lakehouses found")
                return pd.DataFrame()
            
            lakehouses['workspace_id'] = self.workspace_id
            lakehouses['workspace_name'] = self.workspace_name
            lakehouses['scan_timestamp'] = self.timestamp
            
            print(f"  ✓ Found {len(lakehouses)} lakehouses")
            return lakehouses
            
        except Exception as e:
            print(f"  ✗ Error collecting lakehouses: {str(e)}")
            return pd.DataFrame()
    
    def collect_notebooks(self) -> pd.DataFrame:
        """
        Collect information about notebooks
        
        Returns:
            DataFrame with notebook details
        """
        print("\n📓 Collecting notebook details...")
        
        try:
            items = fabric.list_items(workspace=self.workspace_id)
            notebooks = items[items['Type'] == 'Notebook'].copy()
            
            if notebooks.empty:
                print("  ℹ No notebooks found")
                return pd.DataFrame()
            
            notebooks['workspace_id'] = self.workspace_id
            notebooks['workspace_name'] = self.workspace_name
            notebooks['scan_timestamp'] = self.timestamp
            
            print(f"  ✓ Found {len(notebooks)} notebooks")
            return notebooks
            
        except Exception as e:
            print(f"  ✗ Error collecting notebooks: {str(e)}")
            return pd.DataFrame()
    
    def collect_data_pipelines(self) -> pd.DataFrame:
        """
        Collect information about data pipelines
        
        Returns:
            DataFrame with pipeline details
        """
        print("\n⚙️ Collecting data pipeline details...")
        
        try:
            items = fabric.list_items(workspace=self.workspace_id)
            pipelines = items[items['Type'] == 'DataPipeline'].copy()
            
            if pipelines.empty:
                print("  ℹ No data pipelines found")
                return pd.DataFrame()
            
            pipelines['workspace_id'] = self.workspace_id
            pipelines['workspace_name'] = self.workspace_name
            pipelines['scan_timestamp'] = self.timestamp
            
            print(f"  ✓ Found {len(pipelines)} data pipelines")
            return pipelines
            
        except Exception as e:
            print(f"  ✗ Error collecting pipelines: {str(e)}")
            return pd.DataFrame()
    
    def collect_dataflows(self) -> pd.DataFrame:
        """
        Collect information about dataflows
        
        Returns:
            DataFrame with dataflow details
        """
        print("\n🌊 Collecting dataflow details...")
        
        try:
            items = fabric.list_items(workspace=self.workspace_id)
            dataflows = items[items['Type'].isin(['Dataflow', 'DataflowGen2'])].copy()
            
            if dataflows.empty:
                print("  ℹ No dataflows found")
                return pd.DataFrame()
            
            dataflows['workspace_id'] = self.workspace_id
            dataflows['workspace_name'] = self.workspace_name
            dataflows['scan_timestamp'] = self.timestamp
            
            print(f"  ✓ Found {len(dataflows)} dataflows")
            return dataflows
            
        except Exception as e:
            print(f"  ✗ Error collecting dataflows: {str(e)}")
            return pd.DataFrame()
    
    def generate_inventory(self) -> Dict[str, pd.DataFrame]:
        """
        Generate comprehensive inventory of the workspace
        
        Returns:
            Dictionary containing all inventory DataFrames
        """
        print("\n" + "="*60)
        print(f"🚀 STARTING INVENTORY GENERATION")
        print(f"   Workspace: {self.workspace_name}")
        print(f"   Timestamp: {self.timestamp}")
        print("="*60)
        
        # Resolve workspace
        self.resolve_workspace()
        
        # Collect all components
        inventory = {
            'workspace_info': pd.DataFrame([self.collect_workspace_info()]),
            'all_items': self.collect_all_items(),
            'semantic_models': self.collect_semantic_models(),
            'reports': self.collect_reports(),
            'lakehouses': self.collect_lakehouses(),
            'notebooks': self.collect_notebooks(),
            'data_pipelines': self.collect_data_pipelines(),
            'dataflows': self.collect_dataflows()
        }
        
        print("\n" + "="*60)
        print("✅ INVENTORY GENERATION COMPLETE")
        print("="*60)
        
        return inventory
    
    def save_to_lakehouse(self, inventory: Dict[str, pd.DataFrame], 
                         lakehouse_path: str = None) -> None:
        """
        Save inventory to Delta tables in the attached Lakehouse
        
        Args:
            inventory: Dictionary of inventory DataFrames
            lakehouse_path: Optional custom path to lakehouse
        """
        print("\n💾 Saving inventory to Lakehouse Delta tables...")
        
        try:
            # Get the lakehouse path if not provided
            if not lakehouse_path:
                lakehouse_id = fabric.get_lakehouse_id()
                workspace_id = fabric.get_workspace_id()
                lakehouse_path = f"abfss://workspace@onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/Tables"
            
            # Save each DataFrame as a Delta table
            for table_name, df in inventory.items():
                if not df.empty:
                    table_path = f"{lakehouse_path}/fabric_inventory_{table_name}"
                    
                    # Convert to Spark DataFrame and save
                    spark_df = spark.createDataFrame(df)
                    spark_df.write \
                        .mode("overwrite") \
                        .option("overwriteSchema", "true") \
                        .format("delta") \
                        .save(table_path)
                    
                    print(f"  ✓ Saved {table_name} ({len(df)} rows) to Delta table")
                    
        except Exception as e:
            print(f"  ✗ Error saving to lakehouse: {str(e)}")
            print("  ℹ Inventory data is still available in memory")
    
    def display_summary(self, inventory: Dict[str, pd.DataFrame]) -> None:
        """
        Display inventory summary
        
        Args:
            inventory: Dictionary of inventory DataFrames
        """
        print("\n📊 INVENTORY SUMMARY")
        print("="*60)
        
        for name, df in inventory.items():
            if not df.empty:
                print(f"\n{name.upper()}:")
                print(f"  • Records: {len(df)}")
                if 'Type' in df.columns:
                    print(f"  • Types: {', '.join(df['Type'].unique())}")
                
                # Show first few columns as sample
                if len(df.columns) > 0:
                    sample_cols = list(df.columns[:5])
                    print(f"  • Key columns: {', '.join(sample_cols)}")
        
        print("\n" + "="*60)

# ============================================================================
# SECTION 4: MAIN EXECUTION FUNCTION
# ============================================================================

def run_fabric_inventory(
    workspace_name: str,
    auth_method: str = "managed_identity",
    save_to_delta: bool = True,
    **auth_params
) -> Dict[str, pd.DataFrame]:
    """
    Main function to run the Fabric inventory collection
    
    Args:
        workspace_name: Name of the Fabric workspace to inventory
        auth_method: Authentication method ('managed_identity' or 'service_principal')
        save_to_delta: Whether to save results to Delta tables
        **auth_params: Additional authentication parameters
        
    Returns:
        Dictionary containing all inventory DataFrames
    """
    
    # Setup authentication
    authenticator = FabricAuthenticator(auth_method)
    
    if auth_method == "managed_identity":
        authenticator.setup_managed_identity(
            client_id=auth_params.get('client_id')
        )
    elif auth_method == "service_principal":
        authenticator.setup_service_principal_cert(
            tenant_id=auth_params.get('tenant_id'),
            client_id=auth_params.get('client_id'),
            cert_path=auth_params.get('cert_path')
        )
    
    # Create inventory collector
    collector = FabricInventoryCollector(
        workspace_name=workspace_name,
        auth_provider=authenticator
    )
    
    # Generate inventory
    inventory = collector.generate_inventory()
    
    # Save to Delta tables if requested
    if save_to_delta:
        collector.save_to_lakehouse(inventory)
    
    # Display summary
    collector.display_summary(inventory)
    
    return inventory

# ============================================================================
# SECTION 5: USAGE EXAMPLES
# ============================================================================

# Example 1: Using Managed Identity (Recommended for Fabric environment)
# This uses the workspace's managed identity automatically
inventory = run_fabric_inventory(
    workspace_name="YOUR_WORKSPACE_NAME",
    auth_method="managed_identity",
    save_to_delta=True
)

# Example 2: Using Service Principal with Certificate (No secrets)
# inventory = run_fabric_inventory(
#     workspace_name="YOUR_WORKSPACE_NAME",
#     auth_method="service_principal",
#     tenant_id="your-tenant-id",
#     client_id="your-service-principal-id",
#     cert_path="/path/to/certificate.pem",
#     save_to_delta=True
# )

# Example 3: Access specific inventory data
# all_items = inventory['all_items']
# semantic_models = inventory['semantic_models']
# reports = inventory['reports']

# Display sample of semantic models
if not inventory['semantic_models'].empty:
    print("\n📊 Sample Semantic Models:")
    display(inventory['semantic_models'].head())

# Display sample of all items
if not inventory['all_items'].empty:
    print("\n📦 Sample Items:")
    display(inventory['all_items'].head())

print("\n✅ Inventory collection complete!")
print("📝 Data is now available in the 'inventory' dictionary")
print("🔍 Use inventory['table_name'] to access specific data")