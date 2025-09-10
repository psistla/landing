# Microsoft Fabric Workspace Inventory Notebook
# Author: Fabric Engineering Team
# Purpose: Generate comprehensive workspace inventory with metadata
# Requirements: Workspace Admin or Capacity Admin credentials

# %% [markdown]
# # 🚀 Microsoft Fabric Workspace Inventory Generator
# This notebook generates a comprehensive inventory of all Fabric workspaces including:
# - Workspace metadata (name, ID, capacity, state)
# - Item/artifact details (reports, datasets, notebooks, etc.)
# - Ownership and access information
# - Last modified dates and activity metrics

# %% [markdown]
# ## 📦 Setup and Dependencies

# %%
# Core imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# Fabric specific imports
try:
    import sempy.fabric as fabric
    from sempy.fabric import FabricRestClient
    print("✅ Semantic-link (sempy) loaded successfully")
except ImportError:
    print("⚠️ Installing semantic-link...")
    import sys
    !{sys.executable} -m pip install semantic-link --quiet
    import sempy.fabric as fabric
    from sempy.fabric import FabricRestClient
    print("✅ Semantic-link installed and loaded")

# Additional imports for enhanced functionality
try:
    import requests
    from urllib.parse import quote
except ImportError:
    !{sys.executable} -m pip install requests --quiet
    import requests
    from urllib.parse import quote

# %% [markdown]
# ## 🔧 Configuration

# %%
class FabricInventoryConfig:
    """Configuration settings for the inventory collection"""
    
    # API Settings
    BASE_URL = "https://api.fabric.microsoft.com/v1"
    API_VERSION = "v1"
    
    # Collection Settings
    BATCH_SIZE = 100
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # Output Settings
    OUTPUT_FORMAT = "delta"  # Options: 'delta', 'csv', 'parquet'
    OUTPUT_PATH = "/lakehouse/default/Tables/workspace_inventory"
    
    # Feature Flags
    COLLECT_ITEMS = True
    COLLECT_USERS = True
    COLLECT_ACTIVITY = True
    COLLECT_CAPACITIES = True
    
    # Item Types to Collect
    ITEM_TYPES = [
        'Report', 'PaginatedReport', 'Dashboard', 'Dataset', 
        'Dataflow', 'DataflowGen2', 'Notebook', 'SparkJobDefinition',
        'Lakehouse', 'Warehouse', 'SQLEndpoint', 'KQLDatabase',
        'Eventstream', 'KQLQueryset', 'MLModel', 'MLExperiment'
    ]

config = FabricInventoryConfig()

# %% [markdown]
# ## 🏗️ Core Utility Functions

# %%
class FabricAPIHelper:
    """Helper class for Fabric API operations"""
    
    def __init__(self):
        self.client = FabricRestClient()
        self.session = self._get_authenticated_session()
        
    def _get_authenticated_session(self) -> requests.Session:
        """Get an authenticated session using current credentials"""
        session = requests.Session()
        # The FabricRestClient handles authentication
        token = self.client.get_token()
        session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        return session
    
    def make_request(self, endpoint: str, method: str = 'GET', 
                    params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make authenticated API request with retry logic"""
        url = f"{config.BASE_URL}/{endpoint}"
        
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get('Retry-After', config.RETRY_DELAY))
                    print(f"⏳ Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Request failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Request error: {str(e)}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY)
                    
        return None
    
    def get_all_pages(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Get all pages from a paginated endpoint"""
        all_items = []
        continuation_token = None
        
        while True:
            if params is None:
                params = {}
            
            if continuation_token:
                params['continuationToken'] = continuation_token
                
            response = self.make_request(endpoint, params=params)
            
            if not response:
                break
                
            items = response.get('value', [])
            all_items.extend(items)
            
            continuation_token = response.get('continuationToken')
            if not continuation_token:
                break
                
        return all_items

# %% [markdown]
# ## 📊 Data Collection Functions

# %%
class WorkspaceInventoryCollector:
    """Main collector class for workspace inventory"""
    
    def __init__(self):
        self.api_helper = FabricAPIHelper()
        self.workspaces_df = pd.DataFrame()
        self.items_df = pd.DataFrame()
        self.users_df = pd.DataFrame()
        self.capacities_df = pd.DataFrame()
        self.activity_df = pd.DataFrame()
        
    def collect_workspaces(self) -> pd.DataFrame:
        """Collect all workspace metadata"""
        print("📁 Collecting workspaces...")
        
        try:
            # Using semantic-link for workspace list
            workspaces = fabric.list_workspaces()
            
            # Enrich with additional API data
            enriched_workspaces = []
            
            for idx, ws in workspaces.iterrows():
                ws_id = ws['Id']
                ws_data = {
                    'workspace_id': ws_id,
                    'workspace_name': ws.get('Name', ''),
                    'description': ws.get('Description', ''),
                    'type': ws.get('Type', 'Workspace'),
                    'state': ws.get('State', 'Active'),
                    'capacity_id': ws.get('CapacityId', ''),
                    'is_on_dedicated_capacity': ws.get('IsOnDedicatedCapacity', False)
                }
                
                # Get additional details via REST API
                details = self.api_helper.make_request(f"workspaces/{ws_id}")
                if details:
                    ws_data.update({
                        'created_date': details.get('createdDate'),
                        'created_by': details.get('createdBy', {}).get('displayName'),
                        'modified_date': details.get('modifiedDate'),
                        'modified_by': details.get('modifiedBy', {}).get('displayName')
                    })
                
                enriched_workspaces.append(ws_data)
                
            self.workspaces_df = pd.DataFrame(enriched_workspaces)
            print(f"✅ Collected {len(self.workspaces_df)} workspaces")
            
        except Exception as e:
            print(f"❌ Error collecting workspaces: {str(e)}")
            self.workspaces_df = pd.DataFrame()
            
        return self.workspaces_df
    
    def collect_workspace_items(self, workspace_id: str) -> List[Dict]:
        """Collect all items in a workspace"""
        items = []
        
        for item_type in config.ITEM_TYPES:
            try:
                endpoint = f"workspaces/{workspace_id}/items"
                params = {'type': item_type}
                
                type_items = self.api_helper.get_all_pages(endpoint, params)
                
                for item in type_items:
                    item['workspace_id'] = workspace_id
                    item['item_type'] = item_type
                    items.append(item)
                    
            except Exception as e:
                print(f"⚠️ Error collecting {item_type} items: {str(e)}")
                
        return items
    
    def collect_all_items(self) -> pd.DataFrame:
        """Collect items from all workspaces"""
        if not config.COLLECT_ITEMS:
            return pd.DataFrame()
            
        print("📦 Collecting workspace items...")
        all_items = []
        
        for idx, ws in self.workspaces_df.iterrows():
            ws_id = ws['workspace_id']
            ws_name = ws['workspace_name']
            
            print(f"  Processing workspace: {ws_name}")
            items = self.collect_workspace_items(ws_id)
            
            # Enrich items with workspace info
            for item in items:
                item['workspace_name'] = ws_name
                
            all_items.extend(items)
            
        self.items_df = pd.DataFrame(all_items)
        
        if not self.items_df.empty:
            # Clean up columns
            self.items_df['item_id'] = self.items_df['id']
            self.items_df['item_name'] = self.items_df['displayName']
            self.items_df['created_date'] = pd.to_datetime(self.items_df.get('createdDate'), errors='coerce')
            self.items_df['modified_date'] = pd.to_datetime(self.items_df.get('modifiedDate'), errors='coerce')
            
        print(f"✅ Collected {len(self.items_df)} items")
        return self.items_df
    
    def collect_workspace_users(self, workspace_id: str) -> List[Dict]:
        """Collect users/permissions for a workspace"""
        users = []
        
        try:
            endpoint = f"workspaces/{workspace_id}/users"
            workspace_users = self.api_helper.get_all_pages(endpoint)
            
            for user in workspace_users:
                user['workspace_id'] = workspace_id
                users.append(user)
                
        except Exception as e:
            print(f"⚠️ Error collecting users for workspace {workspace_id}: {str(e)}")
            
        return users
    
    def collect_all_users(self) -> pd.DataFrame:
        """Collect users from all workspaces"""
        if not config.COLLECT_USERS:
            return pd.DataFrame()
            
        print("👥 Collecting workspace users...")
        all_users = []
        
        for idx, ws in self.workspaces_df.iterrows():
            ws_id = ws['workspace_id']
            ws_name = ws['workspace_name']
            
            users = self.collect_workspace_users(ws_id)
            
            for user in users:
                user['workspace_name'] = ws_name
                
            all_users.extend(users)
            
        self.users_df = pd.DataFrame(all_users)
        
        if not self.users_df.empty:
            # Clean up columns
            self.users_df['user_email'] = self.users_df.get('emailAddress', '')
            self.users_df['user_name'] = self.users_df.get('displayName', '')
            self.users_df['role'] = self.users_df.get('workspaceRole', '')
            
        print(f"✅ Collected {len(self.users_df)} user assignments")
        return self.users_df
    
    def collect_capacities(self) -> pd.DataFrame:
        """Collect capacity information"""
        if not config.COLLECT_CAPACITIES:
            return pd.DataFrame()
            
        print("⚡ Collecting capacity information...")
        
        try:
            capacities = fabric.list_capacities()
            self.capacities_df = capacities
            print(f"✅ Collected {len(self.capacities_df)} capacities")
        except Exception as e:
            print(f"❌ Error collecting capacities: {str(e)}")
            self.capacities_df = pd.DataFrame()
            
        return self.capacities_df
    
    def generate_summary_stats(self) -> Dict:
        """Generate summary statistics"""
        stats = {
            'collection_timestamp': datetime.now().isoformat(),
            'total_workspaces': len(self.workspaces_df),
            'total_items': len(self.items_df),
            'total_users': len(self.users_df),
            'total_capacities': len(self.capacities_df),
            'workspaces_on_premium': len(self.workspaces_df[self.workspaces_df['is_on_dedicated_capacity'] == True])
        }
        
        if not self.items_df.empty:
            stats['items_by_type'] = self.items_df['item_type'].value_counts().to_dict()
            
        if not self.users_df.empty:
            stats['users_by_role'] = self.users_df['role'].value_counts().to_dict()
            
        return stats
    
    def run_full_inventory(self) -> Dict[str, pd.DataFrame]:
        """Run complete inventory collection"""
        print("🚀 Starting Fabric Workspace Inventory Collection")
        print("=" * 50)
        
        start_time = datetime.now()
        
        # Collect all data
        self.collect_workspaces()
        self.collect_all_items()
        self.collect_all_users()
        self.collect_capacities()
        
        # Generate summary
        stats = self.generate_summary_stats()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 50)
        print("📊 Collection Summary:")
        print(f"  • Duration: {duration:.2f} seconds")
        print(f"  • Workspaces: {stats['total_workspaces']}")
        print(f"  • Items: {stats['total_items']}")
        print(f"  • Users: {stats['total_users']}")
        print(f"  • Capacities: {stats['total_capacities']}")
        
        if 'items_by_type' in stats:
            print("\n📦 Items by Type:")
            for item_type, count in stats['items_by_type'].items():
                print(f"  • {item_type}: {count}")
                
        return {
            'workspaces': self.workspaces_df,
            'items': self.items_df,
            'users': self.users_df,
            'capacities': self.capacities_df,
            'summary': pd.DataFrame([stats])
        }

# %% [markdown]
# ## 📤 Output Functions

# %%
class InventoryExporter:
    """Export inventory data to various formats"""
    
    @staticmethod
    def export_to_delta(data: Dict[str, pd.DataFrame], base_path: str = config.OUTPUT_PATH):
        """Export data to Delta tables"""
        print("\n💾 Exporting to Delta tables...")
        
        for table_name, df in data.items():
            if df.empty:
                continue
                
            table_path = f"{base_path}_{table_name}"
            
            try:
                # Write to Delta format
                df.write.format("delta").mode("overwrite").save(table_path)
                print(f"  ✅ Exported {table_name} to {table_path}")
            except:
                # Fallback to Spark DataFrame if native pandas write fails
                spark_df = spark.createDataFrame(df)
                spark_df.write.format("delta").mode("overwrite").save(table_path)
                print(f"  ✅ Exported {table_name} to {table_path}")
    
    @staticmethod
    def export_to_csv(data: Dict[str, pd.DataFrame], base_path: str = "/lakehouse/default/Files/inventory"):
        """Export data to CSV files"""
        print("\n📄 Exporting to CSV files...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for table_name, df in data.items():
            if df.empty:
                continue
                
            file_path = f"{base_path}_{table_name}_{timestamp}.csv"
            
            try:
                df.to_csv(file_path, index=False)
                print(f"  ✅ Exported {table_name} to {file_path}")
            except Exception as e:
                print(f"  ❌ Failed to export {table_name}: {str(e)}")
    
    @staticmethod
    def create_summary_report(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Create a summary report DataFrame"""
        print("\n📈 Creating summary report...")
        
        report_data = []
        
        # Workspace summary
        if not data['workspaces'].empty:
            for idx, ws in data['workspaces'].iterrows():
                ws_id = ws['workspace_id']
                ws_name = ws['workspace_name']
                
                # Count items
                item_count = 0
                if not data['items'].empty:
                    item_count = len(data['items'][data['items']['workspace_id'] == ws_id])
                
                # Count users
                user_count = 0
                if not data['users'].empty:
                    user_count = len(data['users'][data['users']['workspace_id'] == ws_id])
                
                # Get last modified
                last_modified = ws.get('modified_date', '')
                if not data['items'].empty:
                    ws_items = data['items'][data['items']['workspace_id'] == ws_id]
                    if not ws_items.empty and 'modified_date' in ws_items.columns:
                        last_item_modified = ws_items['modified_date'].max()
                        if pd.notna(last_item_modified):
                            last_modified = max(last_modified, last_item_modified) if last_modified else last_item_modified
                
                report_data.append({
                    'workspace_name': ws_name,
                    'workspace_id': ws_id,
                    'capacity_id': ws.get('capacity_id', ''),
                    'is_premium': ws.get('is_on_dedicated_capacity', False),
                    'state': ws.get('state', 'Active'),
                    'item_count': item_count,
                    'user_count': user_count,
                    'created_date': ws.get('created_date', ''),
                    'created_by': ws.get('created_by', ''),
                    'last_modified': last_modified,
                    'modified_by': ws.get('modified_by', '')
                })
        
        report_df = pd.DataFrame(report_data)
        print(f"✅ Summary report created with {len(report_df)} workspaces")
        
        return report_df

# %% [markdown]
# ## 🎯 Main Execution

# %%
def main():
    """Main execution function"""
    
    # Initialize collector
    collector = WorkspaceInventoryCollector()
    
    # Run inventory collection
    inventory_data = collector.run_full_inventory()
    
    # Create summary report
    summary_report = InventoryExporter.create_summary_report(inventory_data)
    inventory_data['summary_report'] = summary_report
    
    # Export data based on configuration
    if config.OUTPUT_FORMAT == 'delta':
        InventoryExporter.export_to_delta(inventory_data)
    elif config.OUTPUT_FORMAT == 'csv':
        InventoryExporter.export_to_csv(inventory_data)
    else:  # Export both
        InventoryExporter.export_to_delta(inventory_data)
        InventoryExporter.export_to_csv(inventory_data)
    
    # Display summary report
    print("\n" + "=" * 50)
    print("📋 Top 10 Workspaces by Item Count:")
    if not summary_report.empty:
        top_workspaces = summary_report.nlargest(10, 'item_count')[
            ['workspace_name', 'item_count', 'user_count', 'is_premium', 'last_modified']
        ]
        display(top_workspaces)
    
    print("\n✅ Inventory collection complete!")
    
    return inventory_data

# Execute main function
if __name__ == "__main__":
    inventory_results = main()

# %% [markdown]
# ## 🔍 Data Analysis & Insights

# %%
# Analyze collected inventory
if 'inventory_results' in locals() and inventory_results:
    print("📊 Inventory Analysis")
    print("=" * 50)
    
    # Workspace distribution by capacity
    if not inventory_results['workspaces'].empty:
        print("\n📈 Workspace Distribution:")
        capacity_dist = inventory_results['workspaces']['is_on_dedicated_capacity'].value_counts()
        print(f"  • Premium Capacity: {capacity_dist.get(True, 0)}")
        print(f"  • Shared Capacity: {capacity_dist.get(False, 0)}")
    
    # Item type distribution
    if not inventory_results['items'].empty:
        print("\n📦 Top Item Types:")
        item_dist = inventory_results['items']['item_type'].value_counts().head(5)
        for item_type, count in item_dist.items():
            print(f"  • {item_type}: {count}")
    
    # User role distribution
    if not inventory_results['users'].empty:
        print("\n👥 User Role Distribution:")
        role_dist = inventory_results['users']['role'].value_counts()
        for role, count in role_dist.items():
            print(f"  • {role}: {count}")
    
    # Stale workspaces (not modified in 90 days)
    if not inventory_results['summary_report'].empty:
        print("\n⚠️ Potentially Stale Workspaces:")
        summary_df = inventory_results['summary_report'].copy()
        summary_df['last_modified'] = pd.to_datetime(summary_df['last_modified'], errors='coerce')
        
        cutoff_date = datetime.now() - timedelta(days=90)
        stale_ws = summary_df[summary_df['last_modified'] < cutoff_date]
        
        if not stale_ws.empty:
            print(f"  Found {len(stale_ws)} workspaces not modified in 90+ days")
            for idx, ws in stale_ws.head(5).iterrows():
                days_old = (datetime.now() - ws['last_modified']).days
                print(f"  • {ws['workspace_name']}: {days_old} days old")
        else:
            print("  No stale workspaces found")

# %% [markdown]
# ## 🎨 Visualization (Optional)

# %%
# Create visualizations if matplotlib is available
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    if 'inventory_results' in locals() and not inventory_results['items'].empty:
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Item type distribution
        item_counts = inventory_results['items']['item_type'].value_counts().head(10)
        axes[0, 0].barh(item_counts.index, item_counts.values)
        axes[0, 0].set_title('Top 10 Item Types')
        axes[0, 0].set_xlabel('Count')
        
        # Workspace item counts
        if not inventory_results['summary_report'].empty:
            ws_items = inventory_results['summary_report']['item_count'].head(20)
            axes[0, 1].hist(ws_items, bins=20, edgecolor='black')
            axes[0, 1].set_title('Item Count Distribution')
            axes[0, 1].set_xlabel('Number of Items')
            axes[0, 1].set_ylabel('Number of Workspaces')
        
        # User role distribution
        if not inventory_results['users'].empty:
            role_counts = inventory_results['users']['role'].value_counts()
            axes[1, 0].pie(role_counts.values, labels=role_counts.index, autopct='%1.1f%%')
            axes[1, 0].set_title('User Roles')
        
        # Premium vs Shared capacity
        if not inventory_results['workspaces'].empty:
            capacity_counts = inventory_results['workspaces']['is_on_dedicated_capacity'].value_counts()
            axes[1, 1].bar(['Shared', 'Premium'], 
                          [capacity_counts.get(False, 0), capacity_counts.get(True, 0)])
            axes[1, 1].set_title('Capacity Distribution')
            axes[1, 1].set_ylabel('Number of Workspaces')
        
        plt.tight_layout()
        plt.show()
        
except ImportError:
    print("📊 Matplotlib not available. Skipping visualizations.")

# %% [markdown]
# ## 💡 Usage Examples & Next Steps

# %%
print("""
📚 USAGE EXAMPLES:
================

1. Schedule this notebook to run daily/weekly for regular inventory updates
2. Query the Delta tables for specific insights:

   SELECT * FROM workspace_inventory_summary_report 
   WHERE item_count > 50 
   ORDER BY last_modified DESC

3. Set up alerts for:
   - Workspaces not modified in X days
   - Workspaces with no users
   - Items without proper ownership

🚀 NEXT STEPS:
=============
1. Create Power BI report on top of Delta tables
2. Set up automated email notifications
3. Implement data retention policies
4. Add cost analysis based on capacity usage
5. Create workspace health scores
6. Implement automated cleanup for stale items
""")
