# Invincible.Inc — Launch All Servers
# Starts the backend (port 8742), React frontend (5173), and ngrok tunnel.
# Sites are served via the backend at /sites/oracle, /sites/omni, /sites/grid, /sites/invincible

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$invincible = Join-Path $repo "Invincible"

Write-Host ""
Write-Host "=== Invincible.Inc Launch Sequence ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. Backend (FastAPI / uvicorn on port 8742) ─────────────────────────────
Write-Host "[1/3] Starting backend on http://localhost:8742 ..." -ForegroundColor Yellow
$backendJob = Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile", "-Command",
    "cd '$invincible'; .\.venv\Scripts\Activate.ps1; python backend\run.py"
) -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 3

# ── 2. React frontend (Vite on port 5173) ──────────────────────────────────
Write-Host "[2/3] Starting React frontend on http://localhost:5173 ..." -ForegroundColor Yellow
$frontendJob = Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile", "-Command",
    "cd '$invincible\frontend'; npm run dev"
) -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 2

# ── 3. ngrok tunnel (exposes port 8742 publicly) ────────────────────────────
Write-Host "[3/3] Starting ngrok tunnel on port 8742 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Sites available at the ngrok URL:" -ForegroundColor Green
Write-Host "    /sites/oracle      — Oracle marketing site" -ForegroundColor White
Write-Host "    /sites/omni        — Omni operator site" -ForegroundColor White
Write-Host "    /sites/grid        — Grid enterprise site" -ForegroundColor White
Write-Host "    /sites/invincible  — Invincible.Inc parent" -ForegroundColor White
Write-Host "    /                  — Oracle app (React)" -ForegroundColor White
Write-Host ""
Write-Host "  For Twingate access: connect via Twingate client," -ForegroundColor Cyan
Write-Host "  then use http://backend.invincible.lan:8742" -ForegroundColor Cyan
Write-Host ""

ngrok http 8742 --config "$repo\ngrok.yml"
