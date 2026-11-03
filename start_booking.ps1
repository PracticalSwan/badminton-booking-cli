[CmdletBinding()]
param([switch]$SkipAuth)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = 'Badminton Court Booking'
$PauseFile = Join-Path $Root 'PAUSED'
$EnableScript = Join-Path $Root 'enable_booking.ps1'
$AuthMarker = Join-Path $Root 'auth.ok'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Booking = Join-Path $Root 'booking.py'

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    if (!(Test-Path -LiteralPath $EnableScript)) { throw "Missing: $EnableScript" }
    if ($SkipAuth) { & $EnableScript -SkipAuth } else { & $EnableScript }
}
if (!(Test-Path -LiteralPath $AuthMarker)) {
    throw 'Facebook login has not been verified. Run booking.py --login before enabling.'
}
if (!(Test-Path -LiteralPath $Python)) { throw 'Python .venv is missing. Complete README setup first.' }
& $Python $Booking --validate-config
if ($LASTEXITCODE -ne 0) { throw 'Local booking settings are invalid. Task remains paused.' }
# A saved auth.ok marker may outlive a Facebook session: verify access before activating.
& $Python $Booking --check-auth
if ($LASTEXITCODE -ne 0) { throw 'Messenger session verification failed. Run booking.py --login; task not enabled.' }
& (Join-Path $Root 'sync_schedule.ps1')
Enable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if ($task.State -eq 'Disabled') { throw 'Task remains disabled; PAUSED marker preserved.' }
if (Test-Path -LiteralPath $PauseFile) {
    Remove-Item -LiteralPath $PauseFile -Force -ErrorAction Stop
}
if (Test-Path -LiteralPath $PauseFile) { throw 'Pause marker still present.' }
Write-Host "Badminton booking is ACTIVE. Scheduled task: $($task.State)." -ForegroundColor Green
