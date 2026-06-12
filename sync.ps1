$Control = "MISSION_CONTROL.md"
Get-Content CLAUDE.md, GEMINI.md | Set-Content $Control
Copy-Item $Control CLAUDE.md -Force
Copy-Item $Control GEMINI.md -Force
Write-Host "Mission Control Synced." -ForegroundColor Green
