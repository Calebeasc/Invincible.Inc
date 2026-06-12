$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$InfraDir = Join-Path $Root "infrastructure"
$RuntimeDir = Join-Path $env:TEMP "InvincibleColdStart"

function Stop-Port($port) {
    $hits = netstat -ano 2>$null | Select-String ":$port\s" | Where-Object { $_ -match "LISTENING" }
    foreach ($hit in $hits) {
        $processId = ($hit.ToString().Trim() -split '\s+')[-1]
        if ($processId -match '^\d+$' -and $processId -ne '0') {
            Stop-Process -Id ([int]$processId) -Force -ErrorAction SilentlyContinue
        }
    }
}

function Stop-PidFile($name) {
    $pidFile = Join-Path $RuntimeDir "$name.pid"
    if (-not (Test-Path $pidFile)) {
        return
    }

    $processId = Get-Content -Path $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($processId -match '^\d+$') {
        Stop-Process -Id ([int]$processId) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ByPath($fragment) {
    try {
        Get-WmiObject Win32_Process |
            Where-Object { $_.CommandLine -like "*$fragment*" } |
            ForEach-Object { Stop-Process -Id ([int]$_.ProcessId) -Force -ErrorAction SilentlyContinue }
    } catch {}
}

Clear-Host
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Red
Write-Host "   INVINCIBLE.INC SYSTEM SHUTDOWN" -ForegroundColor Red
Write-Host "   Oracle | Omni | Grid | Invincible.Inc" -ForegroundColor White
Write-Host "   $(Get-Date -Format 'yyyy-MM-dd  HH:mm:ss')" -ForegroundColor DarkGray
Write-Host "  ================================================" -ForegroundColor Red
Write-Host ""

$confirm = if ($env:INVINCIBLE_COLDSTART_NONINTERACTIVE -eq "1") { "yes" } else { Read-Host "  Shut down the local stack? (yes / no)" }
if ($confirm -notmatch '^(yes|y)$') {
    Write-Host ""
    Write-Host "  Shutdown cancelled." -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"
    exit 0
}

Write-Host ""
Write-Host "  [1/5] Stopping tracked launcher shells..." -ForegroundColor DarkGray
foreach ($name in @("backend-shell", "shared-frontend-shell", "omni-frontend-shell", "sentinel-shell", "ngrok-shell")) {
    Stop-PidFile -name $name
}

Write-Host "  [2/5] Stopping service ports..." -ForegroundColor DarkGray
foreach ($port in @(8742, 5173, 5174, 9999)) {
    Stop-Port -port $port
}

Write-Host "  [3/5] Stopping any leftover launcher command lines..." -ForegroundColor DarkGray
foreach ($fragment in @(
    "$RuntimeDir\backend.ps1",
    "$RuntimeDir\shared-frontend.ps1",
    "$RuntimeDir\omni-frontend.ps1",
    "$RuntimeDir\sentinel.ps1",
    "$RuntimeDir\ngrok.ps1",
    "spa_proxy_server.py",
    "uvicorn app.main:app --host 0.0.0.0 --port 8742",
    "sentinel_server.py"
)) {
    Stop-ByPath -fragment $fragment
}

Write-Host "  [4/5] Stopping ngrok and Twingate..." -ForegroundColor DarkGray
Stop-Process -Name "ngrok" -Force -ErrorAction SilentlyContinue
$twingateCompose = Join-Path $InfraDir "twingate\docker-compose.yml"
if (Test-Path $twingateCompose) {
    try {
        & docker ps >$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            & docker-compose -f $twingateCompose down >$null 2>$null
        }
    } catch {}
}

Write-Host "  [5/5] Cleaning launcher state..." -ForegroundColor DarkGray
Remove-Item -Path $RuntimeDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  Local stack shutdown complete." -ForegroundColor Green
Write-Host "  Ports released: 8742, 5173, 5174, 9999" -ForegroundColor DarkGray
Write-Host ""
if ($env:INVINCIBLE_COLDSTART_NONINTERACTIVE -ne "1") {
    Read-Host "  Press Enter to close this window"
}
