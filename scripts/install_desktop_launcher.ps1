[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$Target = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Enable Badminton Booking.cmd'
$Manager = Join-Path $Root 'Manage Badminton Booking.cmd'
if (!(Test-Path -LiteralPath $Manager)) { throw "Missing manager launcher: $Manager" }
$lines = @(
    '@echo off'
    'setlocal'
    'title Badminton Booking CLI'
    "call ""$Manager"""
    'set "RC=%ERRORLEVEL%"'
    'exit /b %RC%'
)
Set-Content -LiteralPath $Target -Value $lines -Encoding ASCII
Write-Host 'Desktop booking CLI launcher updated.'
