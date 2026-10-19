<#
Creates a Desktop shortcut that starts FSDIRAS.

The point is that the project folder can live anywhere -- and this one has
already been moved once -- while the way to start it stays in the same place.
The shortcut records the launcher's current location, so moving the project
again just means running this once more.
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Target
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Target)) {
    Write-Host "  Could not find the launcher at:"
    Write-Host "    $Target"
    Write-Host "  Run this from inside the project folder."
    exit 1
}

$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'Start FSDIRAS.lnk'
$projectRoot = Split-Path -Parent $Target

try {
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($linkPath)
    $link.TargetPath = $Target
    # Without this the batch file runs with the Desktop as its working
    # directory. It uses %~dp0 throughout so it would still work, but anything
    # it starts would inherit the wrong folder.
    $link.WorkingDirectory = $projectRoot
    $link.Description = 'Start the FSDIRAS scam detection system'
    $link.IconLocation = "$env:SystemRoot\System32\shell32.dll,14"
    $link.Save()
} catch {
    Write-Host "  Could not create the shortcut: $($_.Exception.Message)"
    exit 1
}

Write-Host "  Done. Look for 'Start FSDIRAS' on your Desktop."
Write-Host ""
Write-Host "  It points at:"
Write-Host "    $Target"
Write-Host ""
Write-Host "  If you move the project folder again, run this once more."
