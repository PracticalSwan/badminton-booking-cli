[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = 'Badminton Court Booking'
$PauseFile = Join-Path $Root 'PAUSED'

$stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
Set-Content -LiteralPath $PauseFile -Value "Paused manually at $stamp. Delete only through start_booking.ps1." -Encoding UTF8

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $task) {
    if ($task.State -eq 'Running') {
        Stop-ScheduledTask -TaskName $TaskName
    }

    Disable-ScheduledTask -TaskName $TaskName | Out-Null
    $task = Get-ScheduledTask -TaskName $TaskName

    if ($task.State -ne 'Disabled') {
        throw "Failed to disable scheduled task '$TaskName'. Current state: $($task.State)"
    }
}

if (!(Test-Path -LiteralPath $PauseFile)) {
    throw 'Pause marker was not created.'
}

Write-Host ''
Write-Host 'Badminton booking is PAUSED indefinitely.' -ForegroundColor Yellow
Write-Host "Pause marker: $PauseFile"

if ($null -eq $task) {
    Write-Host "Scheduled task '$TaskName' is not installed."
} else {
    Write-Host "Scheduled task '$TaskName' is disabled."
}

Write-Host 'Run start_booking.ps1 or Start Badminton Booking.cmd when you want to resume.'
