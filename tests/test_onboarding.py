"""Fresh-install safety checks: no live task, browser, or Messenger access."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import booking
from booking_config import ConfigError, validate_private

ROOT = Path(__file__).resolve().parents[1]


class FirstRunTests(unittest.TestCase):
    def test_synthetic_example_is_schema_valid_but_not_operational(self):
        example = json.loads((ROOT / "booking.private.example.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_private(example), example)
        with patch.object(booking, "load_private", return_value=example):
            with self.assertRaisesRegex(ConfigError, "example Messenger URL"):
                booking.load_operational_private()

    def test_login_rejects_example_without_opening_facebook(self):
        example = json.loads((ROOT / "booking.private.example.json").read_text(encoding="utf-8"))
        with patch.object(booking, "load_private", return_value=example), \
             patch.object(booking, "sync_playwright") as browser:
            with self.assertRaises(ConfigError):
                booking.authenticate()
            browser.assert_not_called()

    def test_realistic_synthetic_values_pass_operational_guard(self):
        configured = {"chat_url": "https://www.facebook.com/messages/t/00000000",
                      "student_ids": ["000001"]}
        with patch.object(booking, "load_private", return_value=configured):
            self.assertEqual(booking.load_operational_private(), configured)

    def test_placeholder_student_id_blocks_operational_guard(self):
        configured = {"chat_url": "https://www.facebook.com/messages/t/00000000",
                      "student_ids": ["000001", "000000"]}
        with patch.object(booking, "load_private", return_value=configured):
            with self.assertRaises(ConfigError):
                booking.load_operational_private()

    def test_install_registration_writes_pause_before_task_register(self):
        content = (ROOT / "enable_booking.ps1").read_text(encoding="utf-8")
        self.assertLess(content.index("Set-Content -LiteralPath $PauseFile"),
                        content.index("Register-ScheduledTask -TaskName"))
        self.assertIn("Disable-ScheduledTask -TaskName $TaskName", content)

    def test_explicit_start_checks_auth_and_config_before_enabling(self):
        content = (ROOT / "start_booking.ps1").read_text(encoding="utf-8")
        self.assertLess(content.index("Test-Path -LiteralPath $AuthMarker"),
                        content.index("Enable-ScheduledTask -TaskName"))
        self.assertLess(content.index("--validate-config"),
                        content.index("--check-auth"))
        self.assertLess(content.index("--check-auth"),
                        content.index("Enable-ScheduledTask -TaskName"))

    @unittest.skipUnless(sys.platform == "win32", "PowerShell 5.1 integration requires Windows")
    def test_initializer_is_paused_and_idempotent_in_isolated_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "scripts").mkdir()
            source = ROOT / "scripts" / "initialize_booking.ps1"
            script = root / "scripts" / source.name
            script.write_bytes(source.read_bytes())
            (root / "booking.private.example.json").write_bytes(
                (ROOT / "booking.private.example.json").read_bytes())
            command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", str(script)]
            first = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(first.returncode, 0, first.stderr)
            private = root / "booking.private.json"
            pause = root / "PAUSED"
            self.assertTrue(pause.is_file())
            self.assertEqual(validate_private(json.loads(private.read_text(encoding="utf-8"))),
                             json.loads(private.read_text(encoding="utf-8")))
            # Repeat after local customization; neither personal data nor pause state changes.
            private.write_text(json.dumps({"chat_url":
                "https://www.facebook.com/messages/t/00000000",
                "student_ids": ["000001"]}), encoding="utf-8")
            pause_before = pause.read_bytes()
            private_before = private.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(private.read_bytes(), private_before)
            self.assertEqual(pause.read_bytes(), pause_before)
            # An existing active installation must not be paused by rerunning setup.
            pause.unlink()
            third = subprocess.run(command, capture_output=True, text=True, timeout=20)
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertEqual(private.read_bytes(), private_before)
            self.assertFalse(pause.exists())

    @unittest.skipUnless(sys.platform == "win32", "PowerShell 5.1 integration requires Windows")
    def test_new_task_registration_stays_paused_with_mocked_scheduler(self):
        """Run real installer logic without registering a Windows task."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "enable_booking.ps1").write_bytes(
                (ROOT / "enable_booking.ps1").read_bytes())
            (root / "schedule.json").write_bytes(
                (ROOT / "tests" / "fixtures" / "schedule.default.json").read_bytes())
            (root / "booking.py").write_text("# synthetic\n", encoding="utf-8")
            (root / "scheduled_run.cmd").write_text("@echo off\n", encoding="ascii")
            python_stub = root / ".venv" / "Scripts" / "python.exe"
            python_stub.parent.mkdir(parents=True)
            python_stub.touch()  # -SkipAuth means this stub is never executed.
            script_path = str(root / "enable_booking.ps1").replace("'", "''")
            pause_path = str(root / "PAUSED").replace("'", "''")
            harness = f"""
$ErrorActionPreference = 'Stop'
$global:MockRegistered = $false
$global:MockState = 'Absent'
function New-ScheduledTaskAction {{
    param($Execute, $WorkingDirectory)
    return [pscustomobject]@{{Name='synthetic action'}}
}}
function New-ScheduledTaskTrigger {{
    param([switch]$Daily, $At)
    return [pscustomobject]@{{Name='synthetic trigger'}}
}}
function New-ScheduledTaskSettingsSet {{
    param([switch]$WakeToRun, [switch]$StartWhenAvailable,
          [switch]$AllowStartIfOnBatteries, [switch]$DontStopIfGoingOnBatteries,
          $ExecutionTimeLimit, $MultipleInstances)
    return [pscustomobject]@{{Name='synthetic settings'}}
}}
function New-ScheduledTaskPrincipal {{
    param($UserId, $LogonType, $RunLevel)
    return [pscustomobject]@{{Name='synthetic principal'}}
}}
function New-ScheduledTask {{
    param($Action, $Trigger, $Settings, $Principal, $Description)
    return [pscustomobject]@{{Name='synthetic task'}}
}}
function Register-ScheduledTask {{
    param($TaskName, $InputObject, [switch]$Force)
    if (!(Test-Path -LiteralPath '{pause_path}')) {{
        throw 'Installer registered before creating PAUSED'
    }}
    $global:MockRegistered = $true
    $global:MockState = 'Ready'
}}
function Disable-ScheduledTask {{
    param($TaskName, $ErrorAction)
    $global:MockState = 'Disabled'
}}
function Get-ScheduledTask {{
    param($TaskName, $ErrorAction)
    return [pscustomobject]@{{State=$global:MockState}}
}}
& '{script_path}' -SkipAuth
if (!$global:MockRegistered -or $global:MockState -ne 'Disabled' -or
    !(Test-Path -LiteralPath '{pause_path}')) {{
    throw 'New task did not remain disabled with PAUSED present'
}}
"""
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", harness],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(sys.platform == "win32", "PowerShell 5.1 integration requires Windows")
    def test_stale_auth_cannot_enable_task_in_isolated_mock(self):
        """Exercise the actual start script with synthetic files and mocked task cmdlets."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "start_booking.ps1"
            original = (ROOT / script.name).read_text(encoding="utf-8")
            python_path = sys.executable.replace("'", "''")
            script.write_text(original.replace(
                "$Python = Join-Path $Root '.venv\\Scripts\\python.exe'",
                f"$Python = '{python_path}'", 1,
            ), encoding="utf-8")
            (root / "booking.py").write_text(
                "import os, sys\n"
                "sys.exit(int(os.environ.get('MOCK_AUTH_EXIT', '1')) "
                "if '--check-auth' in sys.argv else 0)\n",
                encoding="utf-8",
            )
            (root / "sync_schedule.ps1").write_text(
                "Write-Output 'Synthetic scheduler sync only'\n", encoding="utf-8"
            )
            (root / "auth.ok").write_text("synthetic test marker\n", encoding="utf-8")
            pause = root / "PAUSED"
            pause.write_text("synthetic pause\n", encoding="utf-8")
            script_path = str(script).replace("'", "''")
            pause_path = str(pause).replace("'", "''")
            harness = f"""
$ErrorActionPreference = 'Stop'
$global:MockEnabled = $false
$global:MockState = 'Disabled'
function Get-ScheduledTask {{
    param([string]$TaskName, [string]$ErrorAction)
    return [pscustomobject]@{{State=$global:MockState}}
}}
function Enable-ScheduledTask {{
    param([string]$TaskName, [string]$ErrorAction)
    $global:MockEnabled = $true
    $global:MockState = 'Ready'
}}
$env:MOCK_AUTH_EXIT = '1'
try {{
    & '{script_path}' -SkipAuth
    throw 'An expired login was incorrectly accepted'
}} catch {{
    if ($_.Exception.Message -match 'incorrectly accepted') {{ throw }}
}}
if ($global:MockEnabled -or !(Test-Path -LiteralPath '{pause_path}')) {{
    throw 'Failed auth changed enabled or pause state'
}}
$env:MOCK_AUTH_EXIT = '0'
& '{script_path}' -SkipAuth
if (!$global:MockEnabled -or (Test-Path -LiteralPath '{pause_path}')) {{
    throw 'Explicit activation did not enable and unpause'
}}
"""
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", harness],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
