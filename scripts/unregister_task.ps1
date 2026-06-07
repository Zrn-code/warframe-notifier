# Removes the WarframeNotifier scheduled task.
#   powershell -ExecutionPolicy Bypass -File scripts\unregister_task.ps1

$ErrorActionPreference = "Stop"
$TaskName = "WarframeNotifier"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'."
} else {
    Write-Host "Task '$TaskName' not found (nothing to remove)."
}
