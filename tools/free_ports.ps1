<#
Frees the system's ports so a fresh copy can bind to them.

Why this exists separately from Stop FSDIRAS.bat: the launcher cannot simply
call that. Stop matches every process whose command line contains the project
folder -- which includes the launcher itself and the console running it -- so
calling it mid-launch kills the launch. That was observed: the restart branch
fired, reported success, and left nothing running.

So this script walks up from itself first and refuses to touch any ancestor.
Everything else that is either (a) started from this project or (b) holding one
of the ports is taken down, together with its children.

The ancestor walk is what makes it safe; the port sweep is what makes it
sufficient, because uvicorn's reload worker inherits its listening socket and
Windows keeps attributing that socket to the supervisor that created it -- a
process id that may already be gone.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Root,

    [Parameter(Mandatory = $true)]
    [string]$Ports
)

$ErrorActionPreference = 'SilentlyContinue'
$Root = $Root.TrimEnd('\')

$portList = @()
foreach ($part in $Ports.Split(',')) {
    $value = 0
    if ([int]::TryParse($part.Trim(), [ref]$value)) { $portList += $value }
}

# --- everything we must not kill -------------------------------------------
$processes = @{}
foreach ($p in Get-CimInstance Win32_Process) { $processes[[int]$p.ProcessId] = $p }

$protected = [System.Collections.Generic.HashSet[int]]::new()
$walk = $PID
$guard = 0
while ($walk -and $processes.ContainsKey($walk) -and $guard -lt 40) {
    [void]$protected.Add($walk)
    $walk = [int]$processes[$walk].ParentProcessId
    $guard++
}

function Stop-Tree([int]$ProcessId) {
    if ($protected.Contains($ProcessId)) { return $false }
    taskkill /F /T /PID $ProcessId 2>&1 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

$killed = 0

# --- anything started from this project, except our own ancestry -----------
foreach ($p in $processes.Values) {
    if (-not $p.CommandLine) { continue }
    if (-not $p.CommandLine.Contains($Root)) { continue }
    if (Stop-Tree ([int]$p.ProcessId)) { $killed++ }
}

Start-Sleep -Milliseconds 600

# --- then whatever still holds the ports -----------------------------------
foreach ($port in $portList) {
    $owners = Get-NetTCPConnection -LocalPort $port -State Listen |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($owner in $owners) {
        if (Stop-Tree ([int]$owner)) { $killed++ }
    }
}

# --- confirm, rather than assume -------------------------------------------
# A port in TIME_WAIT is fine to rebind; a port still being listened on is not,
# and reporting success then would hand the launcher a failure it cannot see.
for ($attempt = 0; $attempt -lt 10; $attempt++) {
    $busy = @()
    foreach ($port in $portList) {
        if (Get-NetTCPConnection -LocalPort $port -State Listen) { $busy += $port }
    }
    if ($busy.Count -eq 0) {
        Write-Host "  Stopped the earlier copy ($killed process tree(s))."
        exit 0
    }
    Start-Sleep -Milliseconds 700
}

Write-Host ("  Could not free port " + ($busy -join " and ") + ".")
exit 1
