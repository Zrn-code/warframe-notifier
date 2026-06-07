# Registers a Windows Scheduled Task that auto-starts the notifier (background loop)
# whenever you log in. No admin rights or NSSM required.
#
#   Run once:   powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1
#   Remove:     powershell -ExecutionPolicy Bypass -File scripts\unregister_task.ps1

$ErrorActionPreference = "Stop"

$TaskName  = "WarframeNotifier"
$ProjectDir = Split-Path -Parent $PSScriptRoot   # parent of \scripts = project root

# Prefer pythonw.exe (no console window); fall back to python.exe.
$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) { $pythonw = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $pythonw) { throw "Python not found on PATH. Install Python 3.11+ or add it to PATH." }

Write-Host "Project : $ProjectDir"
Write-Host "Python  : $pythonw"

$action  = New-ScheduledTaskAction -Execute $pythonw -Argument "run.py --loop" -WorkingDirectory $ProjectDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -DontStopOnIdleEnd `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)   # no time limit (runs continuously)

# Replace any existing task with the same name.
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Warframe major-events notifier (background loop)" | Out-Null

Write-Host "`nRegistered scheduled task '$TaskName' (starts at logon)."
Write-Host "Start it now without logging out:  Start-ScheduledTask -TaskName $TaskName"
Write-Host "Check it's running:                Get-ScheduledTask -TaskName $TaskName"
Write-Host "Watch activity:                    Get-Content '$ProjectDir\notifier.log' -Wait -Tail 20"
