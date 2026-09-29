<#
Stops everything this project started.

Two details make this harder than it looks, and both were found by a version
of this script that left the API still serving after reporting success:

1. The kill must take the whole process tree. uvicorn's reload mode runs a
   supervisor plus a worker; killing only the console window orphans the
   worker, which keeps the port and keeps answering requests.

2. The port cannot be used to find that orphaned worker. It inherits its
   listening socket, so Windows still reports the socket as owned by the
   supervisor that created it -- a process id that no longer exists. Only
   walking down from the console windows reaches it.

Processes are matched on this project's folder path, so unrelated Python or
Node work elsewhere on the machine is never touched.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

$ErrorActionPreference = 'SilentlyContinue'
$Root = $Root.TrimEnd('\')
$killed = 0

function Stop-Tree([int]$ProcessId) {
    # /T takes the descendants with it, which is the whole point here.
    taskkill /F /T /PID $ProcessId 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

# Pass 1: everything launched from this folder -- console windows, uvicorn,
# Vite -- together with their children.
$targets = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($Root) -and $_.ProcessId -ne $PID }

foreach ($proc in $targets) {
    if (Stop-Tree $proc.ProcessId) { $killed++ }
}

Start-Sleep -Milliseconds 800

# Pass 2: a belt-and-braces sweep of the ports, for anything that survived.
# Second, never first: with the supervisor already gone, nothing respawns.
foreach ($port in 8000, 8001, 5173) {
    $owners = Get-NetTCPConnection -LocalPort $port -State Listen |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        if (Stop-Tree $owner) { $killed++ }
    }
}

if ($killed -eq 0) {
    Write-Host "  Nothing was running."
} else {
    Write-Host "  Stopped $killed process tree(s)."
}

# Report the truth rather than assuming success -- that assumption is exactly
# what made the earlier version wrong.
Start-Sleep -Milliseconds 500
$busy = @()
foreach ($port in 8000, 8001, 5173) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen) { $busy += $port }
}

Write-Host ""
if ($busy.Count -gt 0) {
    Write-Host ("  WARNING: something is still listening on port " + ($busy -join " and ") + ".")
    Write-Host "  Restart your computer if it will not let go."
} else {
    Write-Host "  Clean. Both ports are free."
}
