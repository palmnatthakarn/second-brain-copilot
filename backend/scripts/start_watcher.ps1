$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$logDirectory = Join-Path $projectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

Set-Location $projectRoot
python backend\scripts\watch_markdown.py *>> (Join-Path $logDirectory "markdown-watcher.log")
