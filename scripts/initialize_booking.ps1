[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$Example = Join-Path $Root 'booking.private.example.json'
$Private = Join-Path $Root 'booking.private.json'
$PauseFile = Join-Path $Root 'PAUSED'

if (!(Test-Path -LiteralPath $Example)) { throw 'Missing booking.private.example.json.' }

# Already configured: leave the user's settings and automation state untouched.
if (Test-Path -LiteralPath $Private) {
    Write-Host 'Private configuration already exists. No files or automation state changed.'
    return
}

# Fail closed before copying the sample; never register or enable any task here.
if (!(Test-Path -LiteralPath $PauseFile)) {
    Set-Content -LiteralPath $PauseFile -Value 'New installation is paused until manually enabled.' -Encoding UTF8
}
Copy-Item -LiteralPath $Example -Destination $Private -ErrorAction Stop
Write-Host 'Created local booking.private.json from a synthetic example.'
Write-Host 'PAUSED marker is present. No task was registered, enabled, or sent.'
Write-Host 'Edit the local conversation URL and Student IDs before authentication.'
