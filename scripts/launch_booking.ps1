[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Requirements = Join-Path $Root 'requirements.txt'

Set-Location -LiteralPath $Root

if (!(Test-Path -LiteralPath $Python)) {
    if (!(Get-Command py.exe -ErrorAction SilentlyContinue)) {
        throw 'Python was not found. Install Python 3.12 from python.org (with the py launcher), then reopen this file.'
    }

    $Selected = $null
    foreach ($Version in @('3.12', '3.11', '3.10')) {
        # cmd isolates a missing Python version without PowerShell 5.1 turning stderr into a terminating error.
        & cmd.exe /d /c "py -$Version --version >NUL 2>NUL"
        if ($LASTEXITCODE -eq 0) {
            $Selected = $Version
            break
        }
    }
    if ($null -eq $Selected) {
        throw 'Python 3.10, 3.11, or 3.12 is required. Install Python 3.12 and retry.'
    }
    Write-Host 'First-time setup: creating the local Python environment...'
    & py.exe "-$Selected" -m venv (Join-Path $Root '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}

# Match pinned packages without forcing an internet or pip operation on every launch.
$Packages = & $Python -m pip list --format=json --disable-pip-version-check | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect the local Python environment.' }
$InstallNeeded = $false
foreach ($Line in (Get-Content -LiteralPath $Requirements -Encoding UTF8)) {
    $Entry = $Line.Trim()
    if ($Entry -eq '' -or $Entry.StartsWith('#')) { continue }
    if ($Entry -notmatch '^([a-zA-Z0-9_.-]+)==([a-zA-Z0-9_.-]+)$') {
        throw 'Unsupported requirements.txt entry. Expected pinned package==version.'
    }
    $Name = $Matches[1]
    $Version = $Matches[2]
    if (!@($Packages | Where-Object { $_.name -eq $Name -and $_.version -eq $Version }).Count) {
        $InstallNeeded = $true
        break
    }
}
if ($InstallNeeded) {
    Write-Host 'Installing the required Python packages (first run or repair)...'
    & $Python -m pip install --disable-pip-version-check -r $Requirements
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your network connection and retry.' }
}

# Idempotent: existing users' configuration and RUNNING/PAUSED state stay untouched.
& (Join-Path $PSScriptRoot 'initialize_booking.ps1')
if (!(Test-Path -LiteralPath (Join-Path $Root 'booking.private.json'))) {
    throw 'Local booking configuration is missing. Initialization failed.'
}

& $Python (Join-Path $Root 'booking_manager.py')
if ($LASTEXITCODE -ne 0) { throw 'Booking CLI exited with an error.' }
