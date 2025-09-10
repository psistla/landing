# install module (if needed)
Install-Module -Name MicrosoftPowerBIMgmt -Force

# login (use account with workspace admin)
Connect-PowerBIServiceAccount

$workspaceId = "<workspace-guid-or-name-resolve>"  # you can use Get-PowerBIWorkspace to find it
# If you only have per-user rights, use Get-PowerBIWorkspace to find workspaces you can see
Get-PowerBIWorkspace -Scope Individual | Format-Table -AutoSize

# Invoke the Fabric core items API for that workspace
$uri = "https://api.fabric.microsoft.com/v1/workspaces/$workspaceId/items"
$result = Invoke-PowerBIRestMethod -Url $uri -Method Get
$result.value | ConvertTo-Json | Out-File -FilePath "fabric_items_$workspaceId.json"
