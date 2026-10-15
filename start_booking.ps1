[CmdletBinding()]
param([switch]$SkipAuth)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = 'Badminton Court Booking'
$PauseFile = Join-Path $Root 'PAUSED'
$EnableScript = Join-Path $Root 'enable_booking.ps1'

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    if (!(Test-Path -LiteralPath $EnableScript)) { throw "Missing: $EnableScript" }
    if ($SkipAuth) { & $EnableScript -SkipAuth } else { & $EnableScript }
}
& (Join-Path $Root 'sync_schedule.ps1')
Enable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if ($task.State -eq 'Disabled') { throw 'Task remains disabled; PAUSED marker preserved.' }
if (Test-Path -LiteralPath $PauseFile) {
    Remove-Item -LiteralPath $PauseFile -Force -ErrorAction Stop
}
if (Test-Path -LiteralPath $PauseFile) { throw 'Pause marker still present.' }
Write-Host "Badminton booking is ACTIVE. Scheduled task: $($task.State)." -ForegroundColor Green
