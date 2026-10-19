<#
Exits 0 if any of the given ports is being listened on, 1 if all are free.

Used by the launcher to notice an earlier copy of the system still running.

Ports arrive as one comma-separated string and are split here. Declaring the
parameter as [int[]] looks tidier and does not work: cmd passes
"8000,8001,5173" as a single argument, PowerShell cannot convert that to an
int array, and the script fails before doing anything -- so the caller sees
"no ports busy" every time and the check it was written for never happens.

Written as a script rather than inline in the batch file because cmd mangles
caret continuations and redirection operators inside a quoted PowerShell
string, and the result fails silently halfway through.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Ports
)

$ErrorActionPreference = 'SilentlyContinue'

foreach ($part in $Ports.Split(',')) {
    $port = 0
    if (-not [int]::TryParse($part.Trim(), [ref]$port)) {
        continue
    }
    if (Get-NetTCPConnection -LocalPort $port -State Listen) {
        exit 0
    }
}

exit 1
