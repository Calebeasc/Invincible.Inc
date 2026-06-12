# Invincible.Inc — LATTICE MONITOR: Automation & Intelligence Loop
# Managed by @gemini | Monitored by @overseer
 
$ProjectRoot = "C:\Users\eckel\Documents\Invincible.Inc"
$DraftFile = "$ProjectRoot\DEVDRAFT.md"
$SyncIntervalSec = 300   # 5 minutes for Link Sync
$ScoutIntervalSec = 86400 # 24 hours for Scout Research
 
# Track last execution times and file state
$LastSync = 0
$LastScout = 0
$LastDraftHash = ""
 
Write-Host "--- LATTICE MONITOR INITIALIZED ---" -ForegroundColor Cyan
Write-Host "Sync Mode: Local File-Watcher (DEVDRAFT.md)" -ForegroundColor DarkGray
Write-Host "Sync Interval: 5 minutes" -ForegroundColor DarkGray
Write-Host "Scout Interval: 24 hours" -ForegroundColor DarkGray
 
while ($true) {
    $Now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
 
    # 1. LINK SYNC (@link): High-frequency local file bridge
    if ($Now -ge ($LastSync + $SyncIntervalSec)) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [LINK] Synchronizing with local DevDraft..." -ForegroundColor Yellow
        
        if (Test-Path $DraftFile) {
            $CurrentHash = Get-FileHash $DraftFile | Select-Object -ExpandProperty Hash
            if ($CurrentHash -ne $LastDraftHash) {
                Write-Host "[LINK] CHANGE DETECTED: Parsing for NEW developer instructions..." -ForegroundColor Green
                $Content = Get-Content $DraftFile -Raw
                # Trigger gemini to parse the content and dispatch to @alfred
                gemini "Link sync mode: Parse the following NEW developer instructions from DEVDRAFT.md and dispatch them to @alfred: `r`n`r`n $Content"
                $LastDraftHash = $CurrentHash
            } else {
                Write-Host "[LINK] No changes in DevDraft." -ForegroundColor DarkGray
            }
        } else {
            Write-Host "[LINK] WARNING: DEVDRAFT.md not found in root." -ForegroundColor Red
        }
        $LastSync = $Now
    }
 
    # 2. SCOUT RESEARCH (@scout): 24-hour intelligence intake
    if ($Now -ge ($LastScout + $ScoutIntervalSec)) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [SCOUT] Executing Daily Intelligence Intake..." -ForegroundColor Yellow
        # Delegate to @broker to select the best-fit researcher for today's trend
        gemini "@broker delegate a research task to @scholar, @osint-hunter, @spectral, or @leviathan to find new surveillance strategies and append them to MASS_SURVEILLANCE_STRATEGIES.md."
        $LastScout = $Now
    }
 
    # Sleep 1 minute to check again without high CPU usage
    Start-Sleep -Seconds 60
}
