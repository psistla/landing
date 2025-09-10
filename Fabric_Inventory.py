# %% [markdown]
# Fabric Workspace Inventory notebook
# - Uses semantic-link (sempy) + semantic-link-labs (sempy_labs)
# - Run in a Fabric Python notebook (Data Science experience). No service principal required.
# - Output: /tmp/fabric_inventory_{ts}.csv and Delta table 'fabric_inventory' (if you have a lakehouse attached)

# %% [code]
# If semantic-link / semantic-link-labs are not present in your environment, uncomment the pip install lines.
# In Fabric (Spark 3.4+) semantic-link is usually available by default.
# %pip install -U semantic-link semantic-link-labs

# %% [code]
import sempy.fabric as fabric
import sempy_labs as labs
import pandas as pd
import json
import datetime
import traceback
from typing import Dict, Any, Optional

# A small helper to normalize column names from sempy outputs
def _get_col(df, candidates):
    if df is None:
        return None
    for c in candidates:
        if c in df.columns:
            return c
    return None

# %% [code]
# --- Collector helpers ---
def list_workspaces() -> pd.DataFrame:
    """Return DataFrame of workspaces the current user can access."""
    try:
        df = fabric.list_workspaces()
        # standardize column names
        df.columns = [c if isinstance(c, str) else str(c) for c in df.columns]
        return df
    except Exception as e:
        raise RuntimeError(f"list_workspaces failed: {e}")

def list_items_for_workspace(workspace_id_or_name: str) -> pd.DataFrame:
    """Return DataFrame of items in a workspace. Accepts name or id."""
    try:
        df = fabric.list_items(workspace=workspace_id_or_name)
        return df
    except Exception as e:
        # return empty df with error column for graceful continuation
        return pd.DataFrame({"_error": [f"list_items error: {str(e)}"]})

# %% [code]
# --- Enrichment helpers (type-specific) ---
def enrich_dataset(item_id: str, workspace: str) -> Dict[str, Any]:
    """Try to collect dataset-specific metadata (datasources, refresh history).
    This will succeed only if the running user has adequate permissions on the dataset."""
    out = {}
    try:
        ds = fabric.list_datasources(dataset=item_id, workspace=workspace)
        # convert to JSON string for storage; the df -> records is compact
        out["datasources"] = json.dumps(ds.to_dict(orient="records"), default=str)
    except Exception as e:
        out["datasources_error"] = str(e)

    # refresh history (last run)
    try:
        rh = fabric.list_refresh_requests(dataset=item_id, workspace=workspace)
        # rh might be dataframe-like; keep small summary:
        out["refresh_history_count"] = int(len(rh)) if hasattr(rh, "__len__") else None
        if hasattr(rh, "head"):
            try:
                out["last_refresh_summary"] = json.dumps(rh.head(1).to_dict(orient="records"), default=str)
            except:
                out["last_refresh_summary"] = str(rh.head(1))
    except Exception as e:
        out["refresh_history_error"] = str(e)

    return out

def enrich_report(item_id: str, workspace: str) -> Dict[str, Any]:
    """Report-specific enrichment: which semantic model used, visuals, etc (where available)."""
    out = {}
    try:
        # sempy_labs.report helpers are useful; these can be called by name using sempy_labs.report.* 
        # Here we do a gentle attempt to fetch report-level semantic info using sempy_labs.report wrappers.
        # NOTE: these may raise permission errors for some reports — handled gracefully.
        report_wrapper = labs.report if hasattr(labs, "report") else None
        if report_wrapper is not None:
            try:
                x = report_wrapper.list_report_level_measures(item_id, workspace=workspace)
                out["report_measures_count"] = int(len(x))
            except Exception as e:
                out["report_measures_error"] = str(e)
        else:
            out["report_info_note"] = "sempy_labs.report not available in runtime"
    except Exception as e:
        out["report_enrich_error"] = str(e)
    return out

# Add other enrichers as needed (dataflow, pipeline, lakehouse, notebook) following similar pattern.

# %% [code]
# --- Main inventory run ---
def build_inventory(target_workspaces: Optional[list] = None, save_delta: bool = True, delta_table_name: str = "fabric_inventory") -> pd.DataFrame:
    """
    Scans workspaces you can access and builds an inventory DataFrame.
    - target_workspaces: list of workspace names or ids to limit the run (None => all accessible workspaces)
    - save_delta: if True try labs.save_as_delta_table at the end (requires lakehouse access)
    - returns: pandas.DataFrame
    """
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rows = []
    df_ws = list_workspaces()

    # Decide workspace list
    ws_id_col = _get_col(df_ws, ["Id", "id", "workspaceId", "WorkspaceId", "workspace_id", "WorkspaceId"])
    ws_name_col = _get_col(df_ws, ["Name", "name", "displayName", "DisplayName"])
    df_ws = df_ws.fillna("")

    # Build list of workspace identifiers to iterate
    ws_iter = []
    if target_workspaces:
        # accept names or ids
        for tw in target_workspaces:
            ws_iter.append(tw)
    else:
        # prefer "Id" if present, otherwise Name
        for _, w in df_ws.iterrows():
            wid = None
            if ws_id_col:
                wid = w.get(ws_id_col) or w.get(ws_name_col)
            else:
                wid = w.get(ws_name_col)
            if not wid or pd.isna(wid):
                continue
            ws_iter.append(wid)

    for w in ws_iter:
        try:
            items_df = list_items_for_workspace(w)
            # If items_df contains an _error column, record workspace-level error and skip
            if "_error" in items_df.columns:
                rows.append({
                    "workspace": str(w),
                    "error": items_df["_error"].iloc[0]
                })
                continue

            # normalize typical columns
            item_id_col = _get_col(items_df, ["id", "Id", "Id"])
            item_name_col = _get_col(items_df, ["displayName", "DisplayName", "name"])
            item_type_col = _get_col(items_df, ["type", "Type"])
            folder_col = _get_col(items_df, ["folderId", "folderId"])
            desc_col = _get_col(items_df, ["description", "Description"])
            tags_col = _get_col(items_df, ["tags"])

            for _, it in items_df.iterrows():
                item_id = it[item_id_col] if item_id_col and item_id_col in it else None
                display_name = it[item_name_col] if item_name_col and item_name_col in it else None
                item_type = it[item_type_col] if item_type_col and item_type_col in it else None

                base_row = {
                    "workspace": str(w),
                    "workspace_resolved": None,    # optional later mapping to workspace display name
                    "item_id": str(item_id) if item_id is not None else None,
                    "item_name": str(display_name) if display_name is not None else None,
                    "item_type": str(item_type) if item_type is not None else None,
                    "folder_id": str(it.get(folder_col)) if folder_col and folder_col in it else None,
                    "description": str(it.get(desc_col)) if desc_col and desc_col in it else None,
                    "tags": json.dumps(it.get(tags_col)) if tags_col and tags_col in it else None,
                }

                # type-specific enrichment
                enrichment = {}
                try:
                    if item_type and item_type.lower() in ("semanticmodel", "dataset"):
                        enrichment = enrich_dataset(item_id=item_id, workspace=w)
                    elif item_type and item_type.lower() in ("report", "powerbidashboard", "dashboard"):
                        enrichment = enrich_report(item_id=item_id, workspace=w)
                    # other item types can be enriched similarly...
                except Exception as e:
                    enrichment = {"enrich_error": str(e), "enrich_trace": traceback.format_exc()}

                # combine
                row = {**base_row, **enrichment}
                rows.append(row)

        except Exception as e:
            rows.append({
                "workspace": str(w),
                "error_outer": str(e),
                "trace": traceback.format_exc()
            })

    inv_df = pd.DataFrame(rows)
    # some normalization: add a scan timestamp
    inv_df["scanned_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

    # Save CSV locally in the runtime
    outpath = f"/tmp/fabric_inventory_{ts}.csv"
    try:
        inv_df.to_csv(outpath, index=False)
        print(f"Saved CSV to {outpath}")
    except Exception as e:
        print("Failed saving CSV locally:", e)

    # Save to delta via sempy_labs (optional)
    if save_delta:
        try:
            labs.save_as_delta_table(inv_df, delta_table_name=delta_table_name, write_mode="overwrite")
            print(f"Saved inventory to delta table '{delta_table_name}' in attached lakehouse.")
        except Exception as e:
            print("Delta save failed (maybe no lakehouse attached or permission issue):", e)

    return inv_df

# %% [code]
# Run it (example: all accessible workspaces)
inventory_df = build_inventory(target_workspaces=None, save_delta=True, delta_table_name="fabric_inventory")
inventory_df.head(20)

# %% [markdown]
# Notes:
# - If you want to limit to a couple of workspaces: pass target_workspaces=['Workspace Name', 'workspace-id-guid'] to build_inventory.
# - If you see permission errors (datasources_error, refresh_history_error), that typically means your user lacks the required dataset-level RW/read permissions or the field is admin-only.
