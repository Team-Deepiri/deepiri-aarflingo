# Start Windows webcam bridge for WSL dev (run in PowerShell on Windows host)
param(
    [string]$Source = "0",
    [int]$Port = 8766
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

Write-Host "Aarflingo webcam bridge (Windows host -> WSL runtime)" -ForegroundColor Cyan
Write-Host "  Stream: http://localhost:$Port/video/stream" -ForegroundColor Gray
Write-Host "  WSL:    http://$(hostname):$Port/video/stream or use nameserver IP from WSL" -ForegroundColor Gray

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) { throw "Python not found on Windows PATH" }

& $py.Source -m pip install -q -r "$Root\scripts\webcam\requirements.txt"
& $py.Source "$Root\scripts\webcam\webcam_bridge.py" --source $Source --port $Port --host 0.0.0.0
