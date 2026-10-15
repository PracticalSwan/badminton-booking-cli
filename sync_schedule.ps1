[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Schedule = Join-Path $Root 'schedule.json'
$TaskName = 'Badminton Court Booking'

$config = Get-Content -LiteralPath $Schedule -Raw -Encoding UTF8 | ConvertFrom-Json
$sendText = [string]$config.send_time
if ($sendText -notmatch '^([01][0-9]|2[0-3]):[0-5][0-9]$' -or $sendText -eq '00:00') {
    throw 'Invalid send_time in schedule.json.'
}
$hours = [int]$sendText.Substring(0, 2)
$minutes = [int]$sendText.Substring(3, 2)
$launch = [datetime]::Today.AddHours($hours).AddMinutes($minutes - 1)

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Host 'Schedule saved; Windows scheduled task not installed yet.'
    return
}

$wasDisabled = $task.State -eq 'Disabled'
if ($task.State -eq 'Running') {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction Stop
}
$trigger = New-ScheduledTaskTrigger -Daily -At $launch
Set-ScheduledTask -TaskName $TaskName -Trigger $trigger -ErrorAction Stop | Out-Null

if ($wasDisabled) {
    Disable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null
}
$updated = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
if ($wasDisabled -and $updated.State -ne 'Disabled') {
    throw 'Scheduler became enabled during a disabled-state sync.'
}
$expected = $launch.ToString('HH:mm')
$actual = ([datetime]$updated.Triggers[0].StartBoundary).ToString('HH:mm')
if ($actual -ne $expected) {
    throw "Scheduler trigger mismatch: expected $expected but found $actual."
}
Write-Host "Scheduler launch set to $expected (1 minute before send)."
