<#
.SYNOPSIS
    Microsoft Fabric Workspace Audit Report Generator - Capacity Admin Version
    Uses Capacity Admin privileges for comprehensive workspace auditing without service principals

.DESCRIPTION
    This script leverages Capacity Admin permissions to audit Microsoft Fabric workspaces.
    It uses the current user's credentials (interactive or cached) and provides enhanced
    access to admin APIs for more detailed information.

.PARAMETER TenantId
    Azure AD Tenant ID (optional if using current Azure context)

.PARAMETER WorkspaceFilter
    Filter for workspace names (supports wildcards). Example: "Production*"

.PARAMETER OutputPath
    Path for output files. Defaults to current directory with timestamp folder

.PARAMETER IncludePersonalWorkspaces
    Include personal workspaces in the audit

.PARAMETER ExportFormat
    Export format: Excel, CSV, or Both (default: Both)

.PARAMETER UseAdminAPIs
    Use admin APIs for enhanced information (requires Fabric Admin role)

.PARAMETER SkipAuthentication
    Skip authentication if already connected to Azure

.EXAMPLE
    .\Invoke-FabricAudit.ps1
    # Runs audit with interactive authentication

.EXAMPLE
    .\Invoke-FabricAudit.ps1 -WorkspaceFilter "Prod*" -UseAdminAPIs
    # Audits production workspaces using admin APIs

.NOTES
    Author: Fabric Platform Engineering Team
    Version: 2.0.0
    Requirements: 
    - PowerShell 7.0+
    - Az.Accounts module
    - Capacity Admin or Fabric Admin role (for admin APIs)
    - ImportExcel module (optional, for Excel export)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$TenantId,
    
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceFilter = "*",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath,
    
    [Parameter(Mandatory=$false)]
    [switch]$IncludePersonalWorkspaces,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("Excel", "CSV", "Both", "JSON")]
    [string]$ExportFormat = "Both",
    
    [Parameter(Mandatory=$false)]
    [switch]$UseAdminAPIs,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipAuthentication,
    
    [Parameter(Mandatory=$false)]
    [int]$ThrottleLimit = 10,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# ============================================================================
# Script Configuration
# ============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# API Configuration
$script:Config = @{
    BaseUrl = "https://api.fabric.microsoft.com/v1"
    AdminUrl = "https://api.powerbi.com/v1.0/myorg/admin"
    PowerBIUrl = "https://api.powerbi.com/v1.0/myorg"
    GraphUrl = "https://graph.microsoft.com/v1.0"
    MaxRetries = 3
    PageSize = 100
    ThrottleLimit = $ThrottleLimit
    BatchSize = 50
}

# Artifact type mapping
$script:ArtifactTypes = @{
    "Lakehouse" = @{
        Endpoint = "lakehouses"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "Warehouse" = @{
        Endpoint = "warehouses"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "KQLDatabase" = @{
        Endpoint = "kqldatabases"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "Notebook" = @{
        Endpoint = "notebooks"
        SupportsDataSources = $false
        SupportsPermissions = $true
    }
    "SparkJobDefinition" = @{
        Endpoint = "sparkjobdefinitions"
        SupportsDataSources = $false
        SupportsPermissions = $true
    }
    "DataPipeline" = @{
        Endpoint = "datapipelines"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "Dataflow" = @{
        Endpoint = "dataflows"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "Datamarts" = @{
        Endpoint = "datamarts"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "SemanticModel" = @{
        Endpoint = "datasets"
        SupportsDataSources = $true
        SupportsPermissions = $true
        UsePowerBIAPI = $true
    }
    "Report" = @{
        Endpoint = "reports"
        SupportsDataSources = $false
        SupportsPermissions = $true
        UsePowerBIAPI = $true
    }
    "Dashboard" = @{
        Endpoint = "dashboards"
        SupportsDataSources = $false
        SupportsPermissions = $true
        UsePowerBIAPI = $true
    }
    "Eventstream" = @{
        Endpoint = "eventstreams"
        SupportsDataSources = $true
        SupportsPermissions = $true
    }
    "MLModel" = @{
        Endpoint = "mlmodels"
        SupportsDataSources = $false
        SupportsPermissions = $true
    }
    "MLExperiment" = @{
        Endpoint = "mlexperiments"
        SupportsDataSources = $false
        SupportsPermissions = $true
    }
}

# ============================================================================
# Setup and Initialization
# ============================================================================

# Create output directory with timestamp
if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = Join-Path $PWD "FabricAudit_$timestamp"
}

if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

# Setup logging
$script:LogFile = Join-Path $OutputPath "audit_log.txt"
$script:ErrorLog = Join-Path $OutputPath "errors.json"
$script:Errors = @()

function Write-AuditLog {
    param(
        [string]$Message,
        [ValidateSet("Info", "Warning", "Error", "Success", "Debug")]
        [string]$Level = "Info",
        [switch]$NoConsole
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    
    # Write to log file
    Add-Content -Path $script:LogFile -Value $LogEntry
    
    # Write to console with color
    if (-not $NoConsole) {
        $Color = switch ($Level) {
            "Error" { "Red" }
            "Warning" { "Yellow" }
            "Success" { "Green" }
            "Debug" { "Gray" }
            default { "White" }
        }
        
        if ($Level -eq "Debug" -and -not $Verbose) {
            return
        }
        
        Write-Host $LogEntry -ForegroundColor $Color
    }
}

# ============================================================================
# Module Management
# ============================================================================

function Initialize-RequiredModules {
    Write-AuditLog "Checking required PowerShell modules..." -Level Info
    
    $requiredModules = @(
        @{Name = "Az.Accounts"; MinVersion = "2.0.0"}
    )
    
    $optionalModules = @(
        @{Name = "ImportExcel"; MinVersion = "7.0.0"; Optional = $true}
    )
    
    foreach ($module in $requiredModules) {
        $installed = Get-Module -ListAvailable -Name $module.Name | 
            Where-Object { $_.Version -ge $module.MinVersion }
        
        if (-not $installed) {
            Write-AuditLog "Installing required module: $($module.Name)" -Level Warning
            Install-Module -Name $module.Name -MinimumVersion $module.MinVersion -Force -Scope CurrentUser
        }
        
        Import-Module $module.Name -MinimumVersion $module.MinVersion -ErrorAction Stop
    }
    
    # Check optional modules
    foreach ($module in $optionalModules) {
        $installed = Get-Module -ListAvailable -Name $module.Name
        
        if ($installed) {
            Import-Module $module.Name -ErrorAction SilentlyContinue
            Write-AuditLog "Optional module loaded: $($module.Name)" -Level Debug
        } else {
            Write-AuditLog "Optional module not found: $($module.Name) - Some features may be limited" -Level Debug
        }
    }
    
    Write-AuditLog "Module initialization complete" -Level Success
}

# ============================================================================
# Authentication Functions
# ============================================================================

function Connect-FabricService {
    param(
        [string]$TenantId,
        [switch]$SkipIfConnected
    )
    
    Write-AuditLog "Initializing authentication..." -Level Info
    
    try {
        # Check if already connected
        if ($SkipIfConnected) {
            $context = Get-AzContext -ErrorAction SilentlyContinue
            if ($context) {
                Write-AuditLog "Using existing Azure context: $($context.Account.Id)" -Level Info
                $script:TenantId = $context.Tenant.Id
                return $true
            }
        }
        
        # Connect to Azure
        $connectParams = @{}
        if ($TenantId) {
            $connectParams.TenantId = $TenantId
        }
        
        Write-AuditLog "Authenticating to Azure AD..." -Level Info
        $context = Connect-AzAccount @connectParams -ErrorAction Stop
        
        if ($context) {
            $script:TenantId = $context.Context.Tenant.Id
            Write-AuditLog "Successfully authenticated as: $($context.Context.Account.Id)" -Level Success
            Write-AuditLog "Tenant ID: $($script:TenantId)" -Level Info
            
            # Verify admin permissions
            Test-AdminPermissions
            
            return $true
        }
    }
    catch {
        Write-AuditLog "Authentication failed: $_" -Level Error
        throw
    }
    
    return $false
}

function Get-FabricAccessToken {
    param(
        [ValidateSet("Fabric", "PowerBI", "Graph")]
        [string]$Resource = "Fabric"
    )
    
    $resourceUrl = switch ($Resource) {
        "Fabric" { "https://api.fabric.microsoft.com" }
        "PowerBI" { "https://analysis.windows.net/powerbi/api" }
        "Graph" { "https://graph.microsoft.com" }
    }
    
    try {
        $token = Get-AzAccessToken -ResourceUrl $resourceUrl -ErrorAction Stop
        return $token.Token
    }
    catch {
        Write-AuditLog "Failed to get access token for $Resource : $_" -Level Error
        throw
    }
}

function Test-AdminPermissions {
    Write-AuditLog "Checking admin permissions..." -Level Info
    
    try {
        $headers = @{
            "Authorization" = "Bearer $(Get-FabricAccessToken -Resource PowerBI)"
        }
        
        # Try to access admin API
        $adminTest = Invoke-RestMethod `
            -Uri "$($script:Config.AdminUrl)/capacities?`$top=1" `
            -Headers $headers `
            -Method Get `
            -ErrorAction SilentlyContinue
        
        if ($adminTest) {
            Write-AuditLog "Fabric/Capacity Admin permissions confirmed" -Level Success
            $script:IsAdmin = $true
            return $true
        }
    }
    catch {
        Write-AuditLog "Admin API access not available. Running with standard permissions." -Level Warning
        $script:IsAdmin = $false
    }
    
    return $false
}

# ============================================================================
# API Functions
# ============================================================================

function Invoke-FabricRestMethod {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [hashtable]$Headers,
        [object]$Body,
        [int]$RetryCount = 0,
        [ValidateSet("Fabric", "PowerBI", "Graph")]
        [string]$ApiType = "Fabric"
    )
    
    if (-not $Headers) {
        $token = Get-FabricAccessToken -Resource $ApiType
        $Headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
    }
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            Headers = $Headers
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        Write-AuditLog "API Call: $Method $Uri" -Level Debug
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        
        # Handle rate limiting
        if ($statusCode -eq 429 -and $RetryCount -lt $script:Config.MaxRetries) {
            $retryAfter = $_.Exception.Response.Headers["Retry-After"]
            $waitTime = if ($retryAfter) { [int]$retryAfter } else { [Math]::Pow(2, $RetryCount) }
            
            Write-AuditLog "Rate limited. Waiting $waitTime seconds..." -Level Warning
            Start-Sleep -Seconds $waitTime
            
            return Invoke-FabricRestMethod -Uri $Uri -Method $Method -Headers $Headers `
                -Body $Body -RetryCount ($RetryCount + 1) -ApiType $ApiType
        }
        
        # Handle token expiration
        if ($statusCode -eq 401 -and $RetryCount -eq 0) {
            Write-AuditLog "Token expired, refreshing..." -Level Debug
            $Headers["Authorization"] = "Bearer $(Get-FabricAccessToken -Resource $ApiType)"
            
            return Invoke-FabricRestMethod -Uri $Uri -Method $Method -Headers $Headers `
                -Body $Body -RetryCount ($RetryCount + 1) -ApiType $ApiType
        }
        
        # Log error and continue
        $errorDetails = @{
            Uri = $Uri
            Method = $Method
            StatusCode = $statusCode
            Error = $_.Exception.Message
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        
        $script:Errors += $errorDetails
        Write-AuditLog "API Error: $($_.Exception.Message)" -Level Error
        
        return $null
    }
}

function Get-PagedResults {
    param(
        [string]$Uri,
        [hashtable]$Headers,
        [string]$ApiType = "Fabric"
    )
    
    $results = @()
    $continuationToken = $null
    
    do {
        $requestUri = $Uri
        if ($continuationToken) {
            $separator = if ($Uri.Contains("?")) { "&" } else { "?" }
            $requestUri = "$Uri${separator}continuationToken=$continuationToken"
        }
        
        $response = Invoke-FabricRestMethod -Uri $requestUri -Headers $Headers -ApiType $ApiType
        
        if ($response) {
            if ($response.value) {
                $results += $response.value
            } else {
                $results += $response
            }
            
            $continuationToken = $response.continuationToken
        } else {
            break
        }
        
    } while ($continuationToken)
    
    return $results
}

# ============================================================================
# Workspace Functions
# ============================================================================

function Get-FabricWorkspaces {
    param(
        [string]$Filter = "*",
        [switch]$IncludePersonal,
        [switch]$UseAdminAPI
    )
    
    Write-AuditLog "Retrieving workspaces..." -Level Info
    
    $workspaces = @()
    
    try {
        if ($UseAdminAPI -and $script:IsAdmin) {
            # Use admin API for more details
            Write-AuditLog "Using Admin API for enhanced workspace information" -Level Info
            
            $uri = "$($script:Config.AdminUrl)/workspaces?`$top=$($script:Config.PageSize)&`$expand=users,reports,datasets,dataflows,dashboards"
            $workspaces = Get-PagedResults -Uri $uri -ApiType PowerBI
            
            # Add capacity information
            $capacities = Get-FabricCapacities
            foreach ($ws in $workspaces) {
                $capacity = $capacities | Where-Object { $_.id -eq $ws.capacityId }
                if ($capacity) {
                    $ws | Add-Member -NotePropertyName "capacityName" -NotePropertyValue $capacity.displayName -Force
                    $ws | Add-Member -NotePropertyName "capacitySku" -NotePropertyValue $capacity.sku -Force
                }
            }
        } else {
            # Use standard API
            $uri = "$($script:Config.BaseUrl)/workspaces?`$top=$($script:Config.PageSize)"
            $workspaces = Get-PagedResults -Uri $uri -ApiType Fabric
        }
        
        # Filter workspaces
        if ($Filter -ne "*") {
            $workspaces = $workspaces | Where-Object { $_.displayName -like $Filter }
        }
        
        # Filter personal workspaces
        if (-not $IncludePersonal) {
            $workspaces = $workspaces | Where-Object { $_.type -ne "PersonalGroup" }
        }
        
        Write-AuditLog "Retrieved $($workspaces.Count) workspaces" -Level Success
        return $workspaces
    }
    catch {
        Write-AuditLog "Failed to retrieve workspaces: $_" -Level Error
        throw
    }
}

function Get-FabricCapacities {
    if (-not $script:IsAdmin) {
        return @()
    }
    
    try {
        Write-AuditLog "Retrieving capacity information..." -Level Info
        $uri = "$($script:Config.AdminUrl)/capacities"
        $capacities = Get-PagedResults -Uri $uri -ApiType PowerBI
        
        Write-AuditLog "Retrieved $($capacities.Count) capacities" -Level Debug
        return $capacities
    }
    catch {
        Write-AuditLog "Failed to retrieve capacities: $_" -Level Warning
        return @()
    }
}

# ============================================================================
# Artifact Collection Functions
# ============================================================================

function Get-WorkspaceArtifacts {
    param(
        [object]$Workspace,
        [switch]$Detailed
    )
    
    Write-AuditLog "Processing workspace: $($Workspace.displayName)" -Level Info
    
    $artifacts = @()
    
    try {
        # Get all items in workspace
        $uri = "$($script:Config.BaseUrl)/workspaces/$($Workspace.id)/items?`$top=$($script:Config.PageSize)"
        $items = Get-PagedResults -Uri $uri -ApiType Fabric
        
        Write-AuditLog "Found $($items.Count) items in workspace" -Level Debug
        
        # Process items in parallel batches
        $batches = [System.Collections.ArrayList]::new()
        for ($i = 0; $i -lt $items.Count; $i += $script:Config.BatchSize) {
            $batch = $items[$i..[Math]::Min($i + $script:Config.BatchSize - 1, $items.Count - 1)]
            [void]$batches.Add($batch)
        }
        
        foreach ($batch in $batches) {
            $jobs = @()
            
            foreach ($item in $batch) {
                $jobs += Start-Job -ScriptBlock {
                    param($Item, $Workspace, $Config, $LogFile)
                    
                    # Recreate function in job scope
                    function Get-ArtifactDetails {
                        param($Item, $Workspace)
                        
                        $artifact = [PSCustomObject]@{
                            WorkspaceId = $Workspace.id
                            WorkspaceName = $Workspace.displayName
                            WorkspaceType = $Workspace.type
                            CapacityId = $Workspace.capacityId
                            CapacityName = $Workspace.capacityName
                            ArtifactId = $Item.id
                            ArtifactName = $Item.displayName
                            ArtifactType = $Item.type
                            Description = $Item.description
                            CreatedBy = $null
                            CreatedDate = $null
                            ModifiedBy = $null
                            ModifiedDate = $null
                            Owner = $null
                            Permissions = @()
                            DataSources = @()
                            Dependencies = @()
                            Status = "Active"
                            Size = $null
                            RowCount = $null
                            LastRefresh = $null
                            RefreshSchedule = $null
                            Endorsement = $null
                            SensitivityLabel = $null
                            Tags = @()
                        }
                        
                        # Parse dates
                        if ($Item.createdDateTime) {
                            $artifact.CreatedDate = [DateTime]::Parse($Item.createdDateTime)
                            $artifact.CreatedBy = $Item.createdBy.displayName
                        }
                        
                        if ($Item.modifiedDateTime) {
                            $artifact.ModifiedDate = [DateTime]::Parse($Item.modifiedDateTime)
                            $artifact.ModifiedBy = $Item.modifiedBy.displayName
                        }
                        
                        return $artifact
                    }
                    
                    Get-ArtifactDetails -Item $Item -Workspace $Workspace
                } -ArgumentList $item, $Workspace, $script:Config, $script:LogFile
            }
            
            # Wait for batch to complete
            $jobs | Wait-Job -Timeout 30 | Out-Null
            
            foreach ($job in $jobs) {
                if ($job.State -eq "Completed") {
                    $result = Receive-Job -Job $job
                    if ($result) {
                        $artifacts += $result
                    }
                }
                Remove-Job -Job $job -Force
            }
        }
        
        # Get additional details if requested
        if ($Detailed) {
            foreach ($artifact in $artifacts) {
                Get-ArtifactEnhancedDetails -Artifact $artifact -Workspace $Workspace
            }
        }
        
    }
    catch {
        Write-AuditLog "Error processing workspace $($Workspace.displayName): $_" -Level Error
    }
    
    return $artifacts
}

function Get-ArtifactEnhancedDetails {
    param(
        [object]$Artifact,
        [object]$Workspace
    )
    
    try {
        $typeConfig = $script:ArtifactTypes[$Artifact.ArtifactType]
        
        if (-not $typeConfig) {
            return
        }
        
        # Get permissions
        if ($typeConfig.SupportsPermissions) {
            $permissions = Get-ArtifactPermissions -WorkspaceId $Workspace.id `
                -ArtifactId $Artifact.ArtifactId -ArtifactType $Artifact.ArtifactType
            
            if ($permissions) {
                $Artifact.Permissions = $permissions
                
                # Extract owner
                $owner = $permissions | Where-Object { 
                    $_.principalType -eq "User" -and 
                    ($_.role -eq "Admin" -or $_.permission -eq "Owner")
                } | Select-Object -First 1
                
                if ($owner) {
                    $Artifact.Owner = $owner.identifier
                }
            }
        }
        
        # Get data sources
        if ($typeConfig.SupportsDataSources) {
            $dataSources = Get-ArtifactDataSources -WorkspaceId $Workspace.id `
                -ArtifactId $Artifact.ArtifactId -ArtifactType $Artifact.ArtifactType
            
            if ($dataSources) {
                $Artifact.DataSources = $dataSources
            }
        }
        
        # Get refresh history for datasets
        if ($Artifact.ArtifactType -in @("SemanticModel", "Dataset", "Dataflow")) {
            $refreshInfo = Get-ArtifactRefreshInfo -WorkspaceId $Workspace.id `
                -ArtifactId $Artifact.ArtifactId -ArtifactType $Artifact.ArtifactType
            
            if ($refreshInfo) {
                $Artifact.LastRefresh = $refreshInfo.LastRefresh
                $Artifact.RefreshSchedule = $refreshInfo.Schedule
                
                if ($refreshInfo.LastStatus -ne "Succeeded") {
                    $Artifact.Status = "RefreshFailed"
                }
            }
        }
        
    }
    catch {
        Write-AuditLog "Failed to get enhanced details for $($Artifact.ArtifactName): $_" -Level Debug
    }
}

function Get-ArtifactPermissions {
    param(
        [string]$WorkspaceId,
        [string]$ArtifactId,
        [string]$ArtifactType
    )
    
    try {
        $typeConfig = $script:ArtifactTypes[$ArtifactType]
        $endpoint = $typeConfig.Endpoint
        
        if ($typeConfig.UsePowerBIAPI) {
            $uri = "$($script:Config.PowerBIUrl)/groups/$WorkspaceId/$endpoint/$ArtifactId/users"
            $apiType = "PowerBI"
        } else {
            $uri = "$($script:Config.BaseUrl)/workspaces/$WorkspaceId/$endpoint/$ArtifactId/permissions"
            $apiType = "Fabric"
        }
        
        $response = Invoke-FabricRestMethod -Uri $uri -ApiType $apiType
        
        if ($response.value) {
            return $response.value
        }
        
        return $response
    }
    catch {
        return @()
    }
}

function Get-ArtifactDataSources {
    param(
        [string]$WorkspaceId,
        [string]$ArtifactId,
        [string]$ArtifactType
    )
    
    try {
        $uri = $null
        
        switch ($ArtifactType) {
            "SemanticModel" { 
                $uri = "$($script:Config.PowerBIUrl)/groups/$WorkspaceId/datasets/$ArtifactId/datasources"
                $apiType = "PowerBI"
            }
            "Dataflow" { 
                $uri = "$($script:Config.PowerBIUrl)/groups/$WorkspaceId/dataflows/$ArtifactId/datasources"
                $apiType = "PowerBI"
            }
            "Lakehouse" {
                $uri = "$($script:Config.BaseUrl)/workspaces/$WorkspaceId/lakehouses/$ArtifactId/tables"
                $apiType = "Fabric"
            }
            "Warehouse" {
                $uri = "$($script:Config.BaseUrl)/workspaces/$WorkspaceId/warehouses/$ArtifactId/tables"
                $apiType = "Fabric"
            }
        }
        
        if ($uri) {
            $response = Invoke-FabricRestMethod -Uri $uri -ApiType $apiType
            
            if ($response.value) {
                return $response.value | ForEach-Object {
                    @{
                        Type = $_.datasourceType
                        ConnectionString = $_.connectionDetails.connectionString
                        Database = $_.connectionDetails.database
                        Server = $_.connectionDetails.server
                        Path = $_.connectionDetails.path
                        Kind = $_.kind
                        TableName = $_.name
                    }
                }
            }
        }
    }
    catch {
        return @()
    }
}

function Get-ArtifactRefreshInfo {
    param(
        [string]$WorkspaceId,
        [string]$ArtifactId,
        [string]$ArtifactType
    )
    
    try {
        $endpoint = switch ($ArtifactType) {
            "SemanticModel" { "datasets" }
            "Dataset" { "datasets" }
            "Dataflow" { "dataflows" }
            default { return $null }
        }
        
        # Get refresh history
        $uri = "$($script:Config.PowerBIUrl)/groups/$WorkspaceId/$endpoint/$ArtifactId/refreshes?`$top=1"
        $refreshHistory = Invoke-FabricRestMethod -Uri $uri -ApiType PowerBI
        
        $refreshInfo = @{
            LastRefresh = $null
            LastStatus = $null
            Schedule = $null
        }
        
        if ($refreshHistory.value -and $refreshHistory.value.Count -gt 0) {
            $lastRefresh = $refreshHistory.value[0]
            $refreshInfo.LastRefresh = $lastRefresh.endTime
            $refreshInfo.LastStatus = $lastRefresh.status
        }
        
        # Get refresh schedule
        $scheduleUri = "$($script:Config.PowerBIUrl)/groups/$WorkspaceId/$endpoint/$ArtifactId/refreshSchedule"
        $schedule = Invoke-FabricRestMethod -Uri $scheduleUri -ApiType PowerBI
        
        if ($schedule) {
            $refreshInfo.Schedule = $schedule
        }
        
        return $refreshInfo
    }
    catch {
        return $null
    }
}

# ============================================================================
# Report Generation Functions
# ============================================================================

function Export-FabricAuditReport {
    param(
        [array]$Artifacts,
        [string]$OutputPath,
        [string]$Format = "Both"
    )
    
    Write-AuditLog "Generating audit reports..." -Level Info
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportName = "FabricAudit_$timestamp"
    
    # Generate summary statistics
    $summary = Get-AuditSummary -Artifacts $Artifacts
    
    # Export based on format
    switch ($Format) {
        "CSV" {
            Export-CsvReport -Artifacts $Artifacts -OutputPath $OutputPath -ReportName $reportName
        }
        "Excel" {
            Export-ExcelReport -Artifacts $Artifacts -Summary $summary -OutputPath $OutputPath -ReportName $reportName
        }
        "JSON" {
            Export-JsonReport -Artifacts $Artifacts -Summary $summary -OutputPath $OutputPath -ReportName $reportName
        }
        "Both" {
            Export-CsvReport -Artifacts $Artifacts -OutputPath $OutputPath -ReportName $reportName
            Export-ExcelReport -Artifacts $Artifacts -Summary $summary -OutputPath $OutputPath -ReportName $reportName
        }
    }
    
    # Export error log if any errors occurred
    if ($script:Errors.Count -gt 0) {
        $script:Errors | ConvertTo-Json -Depth 5 | Out-File $script:ErrorLog
        Write-AuditLog "Error log saved to: $script:ErrorLog" -Level Warning
    }
    
    # Display summary
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "AUDIT SUMMARY" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    $summary.GetEnumerator() | Sort-Object Name | ForEach-Object {
        Write-Host "$($_.Key): " -NoNewline -ForegroundColor Yellow
        Write-Host $_.Value -ForegroundColor Green
    }
    
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "`nReports saved to: $OutputPath" -ForegroundColor Green
}

function Export-CsvReport {
    param(
        [array]$Artifacts,
        [string]$OutputPath,
        [string]$ReportName
    )
    
    $csvFile = Join-Path $OutputPath "$ReportName.csv"
    
    $csvData = $Artifacts | Select-Object @{
        Name = 'Workspace ID'; Expression = {$_.WorkspaceId}
    }, @{
        Name = 'Workspace Name'; Expression = {$_.WorkspaceName}
    }, @{
        Name = 'Workspace Type'; Expression = {$_.WorkspaceType}
    }, @{
        Name = 'Capacity ID'; Expression = {$_.CapacityId}
    }, @{
        Name = 'Capacity Name'; Expression = {$_.CapacityName}
    }, @{
        Name = 'Artifact ID'; Expression = {$_.ArtifactId}
    }, @{
        Name = 'Artifact Name'; Expression = {$_.ArtifactName}
    }, @{
        Name = 'Artifact Type'; Expression = {$_.ArtifactType}
    }, @{
        Name = 'Owner'; Expression = {$_.Owner}
    }, @{
        Name = 'Created By'; Expression = {$_.CreatedBy}
    }, @{
        Name = 'Created Date'; Expression = {$_.CreatedDate}
    }, @{
        Name = 'Modified By'; Expression = {$_.ModifiedBy}
    }, @{
        Name = 'Modified Date'; Expression = {$_.ModifiedDate}
    }, @{
        Name = 'Status'; Expression = {$_.Status}
    }, @{
        Name = 'Description'; Expression = {$_.Description}
    }, @{
        Name = 'Data Sources'; Expression = {($_.DataSources | ConvertTo-Json -Compress)}
    }, @{
        Name = 'Permissions Count'; Expression = {$_.Permissions.Count}
    }, @{
        Name = 'Last Refresh'; Expression = {$_.LastRefresh}
    }, @{
        Name = 'Endorsement'; Expression = {$_.Endorsement}
    }, @{
        Name = 'Sensitivity Label'; Expression = {$_.SensitivityLabel}
    }
    
    $csvData | Export-Csv -Path $csvFile -NoTypeInformation
    Write-AuditLog "CSV report exported: $csvFile" -Level Success
}

function Export-ExcelReport {
    param(
        [array]$Artifacts,
        [hashtable]$Summary,
        [string]$OutputPath,
        [string]$ReportName
    )
    
    if (-not (Get-Module -Name ImportExcel -ListAvailable)) {
        Write-AuditLog "ImportExcel module not found. Skipping Excel export." -Level Warning
        Write-AuditLog "Install with: Install-Module ImportExcel" -Level Info
        return
    }
    
    Import-Module ImportExcel
    
    $excelFile = Join-Path $OutputPath "$ReportName.xlsx"
    
    # Main audit data
    $mainData = $Artifacts | Select-Object @{
        Name = 'Workspace'; Expression = {$_.WorkspaceName}
    }, @{
        Name = 'Capacity'; Expression = {$_.CapacityName}
    }, @{
        Name = 'Artifact Name'; Expression = {$_.ArtifactName}
    }, @{
        Name = 'Type'; Expression = {$_.ArtifactType}
    }, @{
        Name = 'Owner'; Expression = {$_.Owner}
    }, @{
        Name = 'Created'; Expression = {$_.CreatedDate}
    }, @{
        Name = 'Modified'; Expression = {$_.ModifiedDate}
    }, @{
        Name = 'Status'; Expression = {$_.Status}
    }, @{
        Name = 'Data Sources'; Expression = {$_.DataSources.Count}
    }, @{
        Name = 'Permissions'; Expression = {$_.Permissions.Count}
    }
    
    # Export main sheet
    $mainData | Export-Excel -Path $excelFile -WorksheetName "Audit Report" `
        -AutoSize -AutoFilter -FreezeTopRow -BoldTopRow `
        -TableStyle Medium2 -Title "Microsoft Fabric Audit Report" `
        -TitleBold -TitleSize 16
    
    # Add summary sheet
    $summaryData = $Summary.GetEnumerator() | ForEach-Object {
        [PSCustomObject]@{
            Metric = $_.Key
            Value = $_.Value
        }
    }
    
    $summaryData | Export-Excel -Path $excelFile -WorksheetName "Summary" `
        -AutoSize -AutoFilter -BoldTopRow -TableStyle Light1
    
    # Add workspace breakdown
    $workspaceBreakdown = $Artifacts | Group-Object WorkspaceName | 
        Select-Object @{Name='Workspace';Expression={$_.Name}}, 
                      @{Name='Artifacts';Expression={$_.Count}},
                      @{Name='Types';Expression={($_.Group.ArtifactType | Select-Object -Unique).Count}} |
        Sort-Object Artifacts -Descending
    
    $workspaceBreakdown | Export-Excel -Path $excelFile -WorksheetName "Workspaces" `
        -AutoSize -AutoFilter -BoldTopRow -TableStyle Medium3
    
    # Add artifact type breakdown
    $typeBreakdown = $Artifacts | Group-Object ArtifactType | 
        Select-Object @{Name='Type';Expression={$_.Name}}, 
                      @{Name='Count';Expression={$_.Count}} |
        Sort-Object Count -Descending
    
    $typeBreakdown | Export-Excel -Path $excelFile -WorksheetName "Types" `
        -AutoSize -AutoFilter -BoldTopRow -TableStyle Medium4 `
        -IncludePivotChart -ChartType ColumnClustered
    
    # Add data sources sheet
    $dataSourcesData = foreach ($artifact in $Artifacts | Where-Object {$_.DataSources.Count -gt 0}) {
        foreach ($ds in $artifact.DataSources) {
            [PSCustomObject]@{
                Workspace = $artifact.WorkspaceName
                Artifact = $artifact.ArtifactName
                Type = $artifact.ArtifactType
                SourceType = $ds.Type
                Server = $ds.Server
                Database = $ds.Database
                TableName = $ds.TableName
            }
        }
    }
    
    if ($dataSourcesData) {
        $dataSourcesData | Export-Excel -Path $excelFile -WorksheetName "Data Sources" `
            -AutoSize -AutoFilter -BoldTopRow -TableStyle Medium5
    }
    
    # Add permissions sheet
    $permissionsData = foreach ($artifact in $Artifacts | Where-Object {$_.Permissions.Count -gt 0}) {
        foreach ($perm in $artifact.Permissions) {
            [PSCustomObject]@{
                Workspace = $artifact.WorkspaceName
                Artifact = $artifact.ArtifactName
                Type = $artifact.ArtifactType
                Principal = $perm.identifier
                PrincipalType = $perm.principalType
                Permission = $perm.role
            }
        }
    }
    
    if ($permissionsData) {
        $permissionsData | Export-Excel -Path $excelFile -WorksheetName "Permissions" `
            -AutoSize -AutoFilter -BoldTopRow -TableStyle Medium6
    }
    
    Write-AuditLog "Excel report exported: $excelFile" -Level Success
}

function Export-JsonReport {
    param(
        [array]$Artifacts,
        [hashtable]$Summary,
        [string]$OutputPath,
        [string]$ReportName
    )
    
    $jsonFile = Join-Path $OutputPath "$ReportName.json"
    
    $report = @{
        Metadata = @{
            GeneratedDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            TenantId = $script:TenantId
            ArtifactCount = $Artifacts.Count
            Version = "2.0.0"
        }
        Summary = $Summary
        Artifacts = $Artifacts
    }
    
    $report | ConvertTo-Json -Depth 10 | Out-File $jsonFile
    Write-AuditLog "JSON report exported: $jsonFile" -Level Success
}

function Get-AuditSummary {
    param([array]$Artifacts)
    
    $summary = @{
        "Total Artifacts" = $Artifacts.Count
        "Total Workspaces" = ($Artifacts | Select-Object -Unique WorkspaceName).Count
        "Unique Artifact Types" = ($Artifacts | Select-Object -Unique ArtifactType).Count
        "Artifacts with Owner" = ($Artifacts | Where-Object {$_.Owner}).Count
        "Artifacts with Data Sources" = ($Artifacts | Where-Object {$_.DataSources.Count -gt 0}).Count
        "Artifacts with Permissions" = ($Artifacts | Where-Object {$_.Permissions.Count -gt 0}).Count
        "Failed Refresh Status" = ($Artifacts | Where-Object {$_.Status -eq "RefreshFailed"}).Count
        "Created Last 30 Days" = ($Artifacts | Where-Object {$_.CreatedDate -gt (Get-Date).AddDays(-30)}).Count
        "Modified Last 7 Days" = ($Artifacts | Where-Object {$_.ModifiedDate -gt (Get-Date).AddDays(-7)}).Count
    }
    
    # Add capacity breakdown if admin
    if ($script:IsAdmin) {
        $capacities = $Artifacts | Group-Object CapacityName | Select-Object Name, Count
        foreach ($cap in $capacities) {
            if ($cap.Name) {
                $summary["Capacity: $($cap.Name)"] = $cap.Count
            }
        }
    }
    
    return $summary
}

# ============================================================================
# Main Execution
# ============================================================================

function Start-FabricAudit {
    $startTime = Get-Date
    
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "Microsoft Fabric Workspace Audit - Capacity Admin Version" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host ""
    
    try {
        # Initialize modules
        Initialize-RequiredModules
        
        # Connect to Fabric
        if (-not $SkipAuthentication) {
            $connected = Connect-FabricService -TenantId $TenantId -SkipIfConnected
            if (-not $connected) {
                throw "Failed to authenticate"
            }
        }
        
        # Get workspaces
        $workspaces = Get-FabricWorkspaces -Filter $WorkspaceFilter `
            -IncludePersonal:$IncludePersonalWorkspaces `
            -UseAdminAPI:$UseAdminAPIs
        
        if ($workspaces.Count -eq 0) {
            Write-AuditLog "No workspaces found matching filter: $WorkspaceFilter" -Level Warning
            return
        }
        
        Write-AuditLog "Processing $($workspaces.Count) workspaces..." -Level Info
        
        # Collect artifacts from all workspaces
        $allArtifacts = @()
        $progress = 0
        
        foreach ($workspace in $workspaces) {
            $progress++
            $percentComplete = [int](($progress / $workspaces.Count) * 100)
            
            Write-Progress -Activity "Auditing Fabric Workspaces" `
                -Status "Processing: $($workspace.displayName)" `
                -PercentComplete $percentComplete `
                -CurrentOperation "Workspace $progress of $($workspaces.Count)"
            
            $artifacts = Get-WorkspaceArtifacts -Workspace $workspace -Detailed
            $allArtifacts += $artifacts
            
            Write-AuditLog "Processed workspace '$($workspace.displayName)': $($artifacts.Count) artifacts" -Level Debug
        }
        
        Write-Progress -Activity "Auditing Fabric Workspaces" -Completed
        
        # Generate reports
        if ($allArtifacts.Count -gt 0) {
            Export-FabricAuditReport -Artifacts $allArtifacts -OutputPath $OutputPath -Format $ExportFormat
        } else {
            Write-AuditLog "No artifacts found to report" -Level Warning
        }
        
        # Calculate execution time
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-AuditLog "`nAudit completed in $($duration.ToString('mm\:ss'))" -Level Success
        Write-AuditLog "Total artifacts processed: $($allArtifacts.Count)" -Level Success
        Write-AuditLog "Output directory: $OutputPath" -Level Success
        
    }
    catch {
        Write-AuditLog "Audit failed: $_" -Level Error
        throw
    }
}

# Run the audit
Start-FabricAudit
