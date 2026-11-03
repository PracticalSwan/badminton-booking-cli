[CmdletBinding()]
param([switch]$SkipAuth)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Booking = Join-Path $Root 'booking.py'
$Runner = Join-Path $Root 'scheduled_run.cmd'
$AuthMarker = Join-Path $Root 'auth.ok'
$PauseFile = Join-Path $Root 'PAUSED'
$Schedule = Join-Path $Root 'schedule.json'
$TaskName = 'Badminton Court Booking'

if (!(Test-Path -LiteralPath $Python)) { throw "Python environment not found: $Python" }
if (!(Test-Path -LiteralPath $Booking)) { throw "Booking script not found: $Booking" }
if (!(Test-Path -LiteralPath $Runner)) { throw "Scheduled runner not found: $Runner" }

if (!$SkipAuth -and !(Test-Path -LiteralPath $AuthMarker)) {
    & $Python $Booking --login
    if ($LASTEXITCODE -ne 0) { throw 'Messenger authentication not verified. Task unchanged.' }
}
$config = Get-Content -LiteralPath $Schedule -Raw -Encoding UTF8 | ConvertFrom-Json
$sendTime = [string]$config.send_time
if ($sendTime -notmatch '^([01][0-9]|2[0-3]):[0-5][0-9]$' -or $sendTime -eq '00:00') {
    throw 'Invalid send_time in schedule.json.'
}
$hours = [int]$sendTime.Substring(0, 2)
$minutes = [int]$sendTime.Substring(3, 2)
$launch = [datetime]::Today.AddHours($hours).AddMinutes($minutes - 1)
$Action = New-ScheduledTaskAction -Execute $Runner -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Daily -At $launch
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description 'Uses local schedule.json to send badminton requests; manages weekly and date overrides.'
# Always register in the paused state. Only start_booking.ps1 may activate sending.
# Write PAUSED before registration so even an immediately triggered task cannot send.
if (!(Test-Path -LiteralPath $PauseFile)) {
    Set-Content -LiteralPath $PauseFile -Value 'Paused during task installation. Enable only through start_booking.ps1.' -Encoding UTF8
}
Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
Disable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null
$registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if ($registered.State -ne 'Disabled') { throw 'Installed task did not remain disabled; PAUSED marker preserved.' }
Write-Host "Task registered PAUSED. Daily launch: $($launch.ToString('HH:mm')); send time: $sendTime (Asia/Bangkok)."
