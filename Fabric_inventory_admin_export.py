# %% [markdown]
# Fabric Workspace Inventory with Admin-Mode & File Export

# %% [code]
import sempy.fabric as fabric
import sempy_labs as labs
import pandas as pd
import json
import datetime
import os
import traceback

# --- Export helpers ---
def export_inventory_file(df: pd.DataFrame, basename: str = "fabric_inventory") -> dict:
    """
    Saves DataFrame to CSV and JSON files in /tmp.
    Returns dict of file paths.
    """
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    paths = {}
    try:
        csv_path = f"/tmp/{basename}_{ts}.csv"
        df.to_csv(csv_path, index=False)
        paths["csv"] = csv_path
        print(f"CSV saved at {csv_path}")
    except Exception as e:
        print("CSV export failed:", e)

    try:
        json_path = f"/tmp/{basename}_{ts}.json"
        df.to_json(json_path, orient="records", indent=2)
        paths["json"] = json_path
        print(f"JSON saved at {json_path}")
    except Exception as e:
        print("JSON export failed:", e)

    return paths

# --- Enrichment helpers ---
def enrich_with_admin(item_id: str, workspace_id: str) -> dict:
    """
    Admin enrichment: requires Fabric admin privileges.
    Returns dict with owner, creator, lineage, etc if available.
    """
    out = {}
    try:
        admin_item = labs.admin.get_item(item=item_id, workspace=workspace_id)
        if isinstance(admin_item, pd.DataFrame):
            # flatten first row
            out.update(admin_item.iloc[0].to_dict())
        else:
            out["admin_info"] = str(admin_item)
    except Exception as e:
        out["admin_error"] = str(e)
    return out

# --- Inventory builder ---
def build_inventory(target_workspaces=None,
                    save_delta=True,
                    delta_table_name="fabric_inventory",
                    admin_mode=False,
                    export_files=True) -> pd.DataFrame:
    """
    Builds inventory of Fabric workspaces and items.
    Parameters:
      - target_workspaces: list of workspace names/ids to limit scope (default: all accessible)
      - save_delta: save to delta table if True
      - delta_table_name: name for delta table
      - admin_mode: if True, try to call admin APIs for richer metadata (requires Fabric admin rights)
      - export_files: if True, save CSV + JSON in /tmp
    """
    from sempy.fabric import list_workspaces, list_items
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rows = []

    ws_df = list_workspaces()
    ws_id_col = "Id" if "Id" in ws_df.columns else "id"
    ws_name_col = "Name" if "Name" in ws_df.columns else "name"
    ws_iter = target_workspaces or ws_df[ws_id_col].tolist()

    for wid in ws_iter:
        try:
            items_df = list_items(workspace=wid)
            for _, row in items_df.iterrows():
                item = {
                    "workspace_id": wid,
                    "workspace_name": ws_df.loc[ws_df[ws_id_col] == wid, ws_name_col].values[0],
                    "item_id": row.get("id"),
                    "item_name": row.get("displayName"),
                    "item_type": row.get("type"),
                    "tags": json.dumps(row.get("tags")),
                    "description": row.get("description"),
                }

                # Optional admin enrichment
                if admin_mode:
                    admin_data = enrich_with_admin(item_id=item["item_id"], workspace_id=wid)
                    item.update(admin_data)

                rows.append(item)
        except Exception as e:
            rows.append({
                "workspace_id": wid,
                "error": str(e),
                "trace": traceback.format_exc()
            })

    inv_df = pd.DataFrame(rows)
    inv_df["scanned_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

    if save_delta:
        try:
            labs.save_as_delta_table(inv_df, delta_table_name=delta_table_name, write_mode="overwrite")
            print(f"Saved to delta table '{delta_table_name}'.")
        except Exception as e:
            print("Delta save failed:", e)

    file_paths = {}
    if export_files:
        file_paths = export_inventory_file(inv_df)

    return inv_df


# df = build_inventory(admin_mode=False, export_files=True)

# Example: download the CSV
# from notebookutils import mssparkutils
# mssparkutils.fs.cp("file:/tmp/fabric_inventory_20250910T120000Z.csv", "abfss://<yourlakehouse>@<storageaccount>.dfs.core.windows.net/exports/fabric_inventory.csv")
