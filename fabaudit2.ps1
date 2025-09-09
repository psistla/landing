<#
Generate-FabricAuditReport-Delegated.ps1
This script logs in as a workspace owner (delegated credentials),
enumerates workspaces the user has access to, and exports artifact audit info to CSV.
#>

param(
  [Parameter(Mandatory=$true)] [string] $TenantId,
  [Parameter(Mandatory=$true)] [string] $ClientId,
  [Parameter(Mandatory=$true)] [string] $RedirectUri,
  [string] $CsvOut = "fabric_audit_report_delegated.csv"
)

# Install MSAL.PS if not installed
if (-not (Get-Module -ListAvailable -Name MSAL.PS)) {
    Install-Module MSAL.PS -Scope CurrentUser -Force
}

# ---- STEP 1: Sign in as workspace owner (interactive or device code flow) ----
$Scopes = "https://analysis.windows.net/powerbi/api/.default"
$Token = Get-MsalToken -ClientId $ClientId -TenantId $TenantId -RedirectUri $RedirectUri -Interactive -Scopes $Scopes

$AccessToken = $Token.AccessToken
$Headers = @{ Authorization = "Bearer $AccessToken" }

# ---- STEP 2: Get all workspaces the user owns or can access ----
$workspacesUrl = "https://api.powerbi.com/v1.0/myorg/groups"
$workspaces = (Invoke-RestMethod -Uri $workspacesUrl -Headers $Headers -Method Get).value

$resultRows = @()

foreach ($ws in $workspaces) {
    Write-Host "Processing workspace: $($ws.name) [$($ws.id)]"

    # ---- Reports ----
    $reportsUrl = "https://api.powerbi.com/v1.0/myorg/groups/$($ws.id)/reports"
    $reports = (Invoke-RestMethod -Uri $reportsUrl -Headers $Headers -Method Get).value
    foreach ($r in $reports) {
        $resultRows += [PSCustomObject]@{
            WorkspaceId   = $ws.id
            WorkspaceName = $ws.name
            ArtifactType  = "Report"
            ArtifactId    = $r.id
            ArtifactName  = $r.name
            Owner         = $r.createdBy
            LastModified  = $r.modifiedDateTime
            DataSources   = ""
            Status        = "Active"
        }
    }

    # ---- Datasets ----
    $datasetsUrl = "https://api.powerbi.com/v1.0/myorg/groups/$($ws.id)/datasets"
    $datasets = (Invoke-RestMethod -Uri $datasetsUrl -Headers $Headers -Method Get).value
    foreach ($ds in $datasets) {
        # Get refresh history (latest)
        $refreshUrl = "https://api.powerbi.com/v1.0/myorg/groups/$($ws.id)/datasets/$($ds.id)/refreshes"
        try {
            $refreshes = (Invoke-RestMethod -Uri $refreshUrl -Headers $Headers -Method Get).value
            $lastRefresh = $refreshes | Sort-Object endTime -Descending | Select-Object -First 1
            $refreshStatus = $lastRefresh.status
            $refreshTime   = $lastRefresh.endTime
        } catch {
            $refreshStatus = "N/A"
            $refreshTime   = ""
        }

        $resultRows += [PSCustomObject]@{
            WorkspaceId   = $ws.id
            WorkspaceName = $ws.name
            ArtifactType  = "Dataset"
            ArtifactId    = $ds.id
            ArtifactName  = $ds.name
            Owner         = $ds.configuredBy
            LastModified  = $ds.addedDate
            DataSources   = ($ds.dataSources -join ";")
            Status        = $refreshStatus
        }
    }

    # ---- Dataflows ----
    $dfUrl = "https://api.powerbi.com/v1.0/myorg/groups/$($ws.id)/dataflows"
    try {
        $dataflows = (Invoke-RestMethod -Uri $dfUrl -Headers $Headers -Method Get).value
        foreach ($df in $dataflows) {
            $resultRows += [PSCustomObject]@{
                WorkspaceId   = $ws.id
                WorkspaceName = $ws.name
                ArtifactType  = "Dataflow"
                ArtifactId    = $df.objectId
                ArtifactName  = $df.name
                Owner         = $df.createdBy
                LastModified  = $df.modifiedDateTime
                DataSources   = ""
                Status        = "Active"
            }
        }
    } catch {
        Write-Warning "No dataflows in workspace $($ws.name)"
    }

    # ---- Fabric Items (generic) ----
    $itemsUrl = "https://api.fabric.microsoft.com/v1/workspaces/$($ws.id)/items"
    try {
        $items = (Invoke-RestMethod -Uri $itemsUrl -Headers $Headers -Method Get).value
        foreach ($it in $items) {
            $resultRows += [PSCustomObject]@{
                WorkspaceId   = $ws.id
                WorkspaceName = $ws.name
                ArtifactType  = $it.type
                ArtifactId    = $it.id
                ArtifactName  = $it.displayName
                Owner         = $it.creatorPrincipal.displayName
                LastModified  = $it.lastUpdatedDate
                DataSources   = ""
                Status        = $it.state
            }
        }
    } catch {
        Write-Warning "No Fabric items endpoint available in workspace $($ws.name)"
    }
}

# ---- STEP 3: Export to CSV ----
$resultRows | Export-Csv -Path $CsvOut -NoTypeInformation -Force
Write-Host "Audit report exported to $CsvOut with $($resultRows.Count) rows."
