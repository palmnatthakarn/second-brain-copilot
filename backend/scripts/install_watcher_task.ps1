$ErrorActionPreference = "Stop"
$launcher = Join-Path $PSScriptRoot "start_watcher.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$launcher`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName "SecondBrainMarkdownWatcher" -Action $action -Trigger $trigger -Settings $settings -Description "Synchronizes the Obsidian Markdown vault with PostgreSQL." -Force | Out-Null
Write-Output "Scheduled task installed: SecondBrainMarkdownWatcher"
