Write-Host "Booting Sovereign Sentinel..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python 'C:\Users\eckel\Documents\Invincible.Inc\sentinel_monitor\sentinel_server.py'" -WindowStyle Normal
