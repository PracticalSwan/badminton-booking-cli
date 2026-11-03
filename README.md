# Badminton Booking CLI

Windows-only, text-based automation for sending badminton court booking requests through Facebook Messenger. Each installation uses **its owner's Facebook account, Messenger conversation, Student IDs, and schedule**. No Facebook password is stored in the program. **Messages are not sent during setup or authentication checks.**

> **Access:** This GitHub repository is private. Ask the owner for GitHub collaborator access before cloning. This guide does not require or include the original author's private settings or browser profile.

## Quick start: one file

**After you have downloaded or cloned this repository**, double-click **`Enable Badminton Booking.cmd`** in the project folder. If you already have the Desktop launcher with the same name, use that instead.

On first launch, it creates `.venv`, installs the pinned Python packages if needed, and makes your **local-only** settings file. It starts **PAUSED**: nothing is booked or sent automatically. Subsequent launches keep your configured schedule, Facebook session, Student IDs, and running/paused state unchanged.

The main menu is intentionally short:

| Menu | What to do |
| --- | --- |
| **1** | View booking status and schedule |
| **2** | Edit weekly bookings, date-specific skips/overrides, or send time |
| **3** | Set your own Messenger conversation URL, enter Student IDs, and log in/check login |
| **4** | View or edit your Student IDs (fully visible on your local console) |
| **5** | Start automatic booking, with explicit `YES` confirmation |
| **6** | Pause automatic booking indefinitely |
| **0** | Exit without changing the booking state |

**RUNNING** means automatic booking is enabled and waiting for its scheduled send time, not that a court is already booked. **PAUSED** means automatic booking is not enabled.

For a new installation: choose **3** to enter your own Messenger conversation URL and Student IDs, then log in to your own Facebook account in the Chrome window. Choose **2** to set your weekly booking schedule and sending time. Choose **5** only when ready to begin automatic booking. You can always choose **6** to pause indefinitely.

**Before running the launcher:** install Python 3.10–3.12 (3.12 recommended) with the Windows `py` launcher, and Google Chrome. Git is needed only if you clone or contribute using Git. If you are cloning the private repository, you must have collaborator access. Detailed manual setup and troubleshooting follow.

## 1. Prerequisites (Windows)

- Windows 10/11 with Windows PowerShell 5.1, Task Scheduler, and an interactive Windows user session.
- **Python 3.12** with the Windows `py` launcher (the GitHub Actions test environment uses 3.12). Get it from [python.org](https://www.python.org/downloads/windows/). Python 3.10+ is required by the syntax, but 3.12 is recommended.
- **Google Chrome (Stable)**, installed locally from [google.com/chrome](https://www.google.com/chrome/). The sender launches the installed browser using Playwright's `channel="chrome"`. A separate Playwright Chromium download is **not** required; `playwright install` alone does not replace the Chrome requirement.
- **Git for Windows** from [git-scm.com](https://git-scm.com/download/win), plus access to this private repository. A GitHub ZIP download is an alternative once granted access, but Git is needed for the included privacy audit and version control.
- A Facebook account that can open the **specific Messenger conversation** to which you are authorized to send booking requests.

The Python sender interprets times in **Asia/Bangkok**. Windows Task Scheduler uses the **computer's local time zone**. For correct scheduling, this Windows computer must also use Bangkok time (UTC+07:00). Check with `Get-TimeZone` in PowerShell; changing the computer's time zone is a separate system-wide decision.

The scheduled task runs only for the configured interactive Windows user. Keep that user signed in, the computer awake, and the network available near send time. Delivery and actual court availability are not guaranteed.

## 2. Download and prepare the project

**Optional manual setup (for troubleshooting or contributors):** Normal users can skip these commands and simply double-click `Enable Badminton Booking.cmd` after downloading the repository. If you prefer manual setup, open **Windows PowerShell** and run the following. All later commands assume PowerShell is in the repository root, the directory containing `booking.py` and `requirements.txt`:

~~~powershell
git clone https://github.com/PracticalSwan/badminton-booking-cli.git
Set-Location .\badminton-booking-cli
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\initialize_booking.ps1
~~~

If you downloaded the repository as a ZIP, extract it, open PowerShell in that extracted project directory and skip the `git clone` command. The `py -3.12` command requires the Python 3.12 Windows launcher; check with `py -3.12 --version`. **Do not copy another user's `.venv`, browser profiles, or private configuration.**

The initializer creates **`PAUSED`** and copies `booking.private.example.json` to the ignored local file `booking.private.json`. It does **not** create a Windows task, open Facebook, or enable sending. If `booking.private.json` already exists, initialization leaves **both the private settings and automation state unchanged**, so it is safe to rerun during an existing installation.

## 3. Configure your own Messenger conversation and Student IDs

Open the newly created file locally:

~~~powershell
notepad .\booking.private.json
~~~

The initial file contains only **synthetic values**:

~~~json
{
  "chat_url": "https://www.facebook.com/messages/t/0000000",
  "student_ids": [
    "000000"
  ]
}
~~~

**Replace both example values before continuing.** To find **your own** conversation URL, sign into Facebook in an ordinary Chrome window, open Messenger, select the intended Sports Center conversation, and copy the direct conversation URL from the address bar. It must have this exact structure: `https://www.facebook.com/messages/t/` followed by numeric conversation digits. Use your **own conversation**, never the author's. The program rejects other domains, group links, query parameters, and nonnumeric recipient paths.

Replace `000000` with your own Student ID as a **quoted string of digits**. You may add more IDs, separated by commas; IDs must be unique, contain 1–16 ASCII digits, and the list cannot be empty. Do **not** put Facebook passwords, cookies, access tokens, or other people's IDs in the file. Save it as UTF-8 JSON with proper quotes and commas.

The example is valid JSON and passes the structural validator, but the sender, authentication flow, and validation command **reject unchanged example URL/ID values** to prevent their accidental use. Validate your new settings without visiting Facebook:

~~~powershell
.\.venv\Scripts\python.exe booking.py --validate-config
.\.venv\Scripts\python.exe booking.py --self-test
~~~

`--validate-config` validates the schedule and private settings (no IDs or recipient URL printed). `--self-test` validates and summarizes **only** the current weekly schedule and overrides; neither command sends a message.

## 4. Set your booking schedule

Launch the CLI from PowerShell:

~~~powershell
.\.venv\Scripts\python.exe booking_manager.py
~~~

Or double-click **Enable Badminton Booking.cmd** (the recommended launcher). Use the simplified main menu:

| Choice | Purpose |
| --- | --- |
| 1 | View current RUNNING/PAUSED status, weekly schedule, and date overrides |
| 2 | Open the schedule submenu: weekly slots, date overrides/skips, and daily send time |
| 3 | Configure your Messenger conversation, enter Student IDs, or log in/check login |
| 4 | Show, replace, add, or remove Student IDs |
| 5 | Start automatic sending (requires typing `YES`) |
| 6 | Pause sending indefinitely |
| 0 | Exit without changing the task's state |

The versioned sample schedule uses **08:00 Bangkok time** for sending; the initial weekday bookings are Monday–Friday 16:30–18:00, Sunday 15:30–17:00, and Saturday skipped. **Set your own days and court hours before enabling.** Your schedule is saved in `schedule.json`. Date-specific overrides (`YYYY-MM-DD`) take priority; a skipped day has `null` rather than a slot.

In main-menu **2**, choose **1** for weekly slots, **2** for a date-specific booking or skip, **3** to remove a date override, or **4** for the daily send time. Select **0** to return to the main menu.

All times use 24-hour `HH:MM`. Send time must be from `00:01` to `23:59`. Court bookings must start and end on the same date and have an end time after the start. When changing send time, the CLI updates the existing Windows trigger if installed without changing its enabled/disabled state.

### Editing Student IDs later

Select **4** in the CLI. The submenu displays **complete Student IDs locally**, with list positions, and supports replace, add, or remove. Replacement and addition use **visible double-entry confirmation**, and removal requires typing `REMOVE`. This is intentional: do not screenshot, screen-share, or publish this submenu with actual IDs visible. Editing IDs retains your Messenger URL and does **not** enable automation. If private settings change while a message is being prepared, the sender cancels the stale message.

## 5. Authenticate your own Facebook account (no sending)

From the single launcher, select **3** to enter your own Messenger conversation URL and Student IDs; when prompted, choose to open Chrome for manual login. To check a saved session later, use **3 → 3** (non-sending). If you prefer the manual command line, with Chrome installed and `booking.private.json` configured, run:

~~~powershell
.\.venv\Scripts\python.exe booking.py --login
~~~

A Chrome window opens using a **separate, local, persistent profile** under `chrome_profile/`. Sign in manually to **your own** Facebook account in that window and open/confirm your intended conversation. Return to PowerShell and press Enter when prompted. The script revisits the conversation and checks for a Messenger text composer, writes a local `auth.ok` marker only on successful verification, and closes the window. **Do not type your Facebook password in PowerShell or store it in JSON.**

Check the saved login before enabling:

~~~powershell
.\.venv\Scripts\python.exe booking.py --check-auth
~~~

This also opens Chrome briefly, checks that the composer is available, and closes without typing or sending any message. Avoid opening two automation/profile Chrome instances simultaneously. These checks confirm page access, **not** successful future message delivery or a confirmed badminton reservation.

## 6. Register a paused Windows task and install a Desktop launcher

From the project root:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\enable_booking.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_desktop_launcher.ps1
~~~

These commands are optional when using the single-launcher menu; option **5** registers a missing task as part of starting automation. For manual setup, the first command installs/updates the **Badminton Court Booking** Windows Scheduled Task and **always leaves it disabled with `PAUSED` present**. It never activates a fresh installation. The task starts one minute before the daily send time, but does not send while paused. The second command creates/overwrites **Enable Badminton Booking.cmd** on *your* Windows Desktop; despite its historical name, that launcher now **opens the CLI menu**, not the sender or the enable action. Do not run the Desktop installer if you need to preserve an unrelated file with the same Desktop name.

Both scripts operate on the current Windows user's environment; do not register the task under somebody else's Windows account. There is one task with this name per Windows machine, so separate clones using the same task name can conflict.

Inspect the task and pause state safely:

~~~powershell
Get-ScheduledTask -TaskName 'Badminton Court Booking' | Select-Object TaskName, State
Test-Path .\PAUSED
~~~

Expected after first installation: task **Disabled**, and `Test-Path` returns **True**.

## 7. Enable, pause, and operate

**Only when your schedule, recipient, IDs, and Facebook login are correct**, select **5** in the CLI and type `YES`. Alternatively run:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start_booking.ps1
~~~

The enable script requires the local login marker, validates your configuration, and runs a fresh, **non-sending** Messenger `--check-auth` (which briefly opens Chrome) before synchronizing the trigger. It enables the Windows task and removes `PAUSED` only after successful verification. An expired or inaccessible Facebook session **blocks activation**; run `--login` again, then retry. It does **not** immediately send a booking message; the scheduled run handles the configured time.

To stop bookings **indefinitely**, choose **6** in the CLI or run:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\stop_booking.ps1
~~~

This creates `PAUSED`, stops any running scheduled task, and disables it. Restarting Windows or changing schedule/IDs does not automatically resume a paused installation. Do not manually delete `PAUSED`; use the enable control when you deliberately want to resume.

The sender also enforces one successful submission attempt per date, a **five-minute cutoff** after the send time, and final rechecks for pause/schedule/private-setting changes before pressing Enter. A corrupted `state.json` blocks sending to avoid duplicates. Never use `booking.py` without an option for a "test": on an active installation it is the **real sender**.

## 8. Troubleshooting

| Symptom | What to check |
| --- | --- |
| `git clone` says repository not found or access denied | Request collaborator access, accept the GitHub invitation and authenticate Git for Windows with your **own** GitHub account |
| `py -3.12` or `.venv\Scripts\python.exe` is missing | Install Python 3.12 with the Windows launcher, create `.venv`, and run the pinned `pip install -r requirements.txt` step again |
| Playwright cannot launch `channel="chrome"` | Install or repair **Google Chrome Stable** on Windows; the project does not use the downloaded Playwright Chromium channel |
| `--validate-config` fails | Check JSON syntax, the HTTPS numeric Facebook conversation path, unique quoted numeric Student IDs, and replacement of **both** synthetic example values |
| `--login` or `--check-auth` cannot find a composer | Log in again with `--login`, confirm that **your** Messenger conversation loads, close other automation Chrome instances, and check whether Facebook's page or login flow has changed |
| Task is missing or Disabled | First register with `enable_booking.ps1`. Enabling requires an explicit CLI `YES` or `start_booking.ps1`, valid private settings, and a currently working Messenger session; a Disabled task with `PAUSED` is intentional |
| Task starts at the wrong clock time | Check Windows `Get-TimeZone`, schedule `send_time`, and the scheduled trigger (one minute earlier). Windows local time must match Bangkok for the documented behavior |
| Task cannot register or is denied access | Run PowerShell under the intended interactive Windows account; inspect Windows Task Scheduler permissions and avoid accidentally switching to another account |
| Task is Ready but no booking was sent | Inspect **local-only** `booking.log`/`task_console.log`, login state, current date skip/override, five-minute cutoff, and sleep/network interruptions. `Ready` alone does not confirm successful sending |
| Corrupt `state.json` causes a blocked send | Stop automation first. Reconcile booking history and actual Messenger messages before restoring a known-correct local state; blindly deleting the file can cause duplicate requests |

If your Facebook session expires, run `--login` again, followed by `--check-auth`. If Chrome or Messenger changes its interface, the composer locator may require a code update. No automated test can guarantee Facebook will keep the same UI.

## 9. Privacy and maintenance

Keep **`booking.private.json`**, `auth.ok`, `PAUSED`, `state.json`, `chrome_profile/`, `browser_profile/`, `.venv/`, cookies, and logs **on your own computer only**. They are listed in `.gitignore`. Never upload them to GitHub, issues, support requests, chat, or screenshots, even if the repository remains private.

`schedule.json` is version-controlled, so your customized slots may appear as a local Git modification. Only commit it when you intentionally want to share those scheduling choices; it is not needed to publish general setup improvements.

To run synthetic tests from the project root (they do **not** send Messenger messages):

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe booking.py --self-test
~~~

For contributors using Git, review **only intended source files** before committing. After explicit staging, run:

~~~powershell
.\.venv\Scripts\python.exe scripts\privacy_check.py
git diff --cached --name-only
git status --short
~~~

The privacy check audits tracked/staged Git blobs for blocked paths and likely identity values; it is defense-in-depth, not a replacement for careful review. Do not use `git add .` if your own local schedule or unrelated files must stay out of the commit.

### Main files

| File | Responsibility |
| --- | --- |
| `Enable Badminton Booking.cmd` | Recommended single-click entry point; opens safe setup and CLI controls |
| `Manage Badminton Booking.cmd` / `scripts/launch_booking.ps1` | Initializes the local Python environment and runs the CLI; does not enable sending |
| `booking.py` | Manual login, non-sending checks, Messenger sender, safety gates |
| `booking_manager.py` | Interactive text menu and locally visible Student ID editing |
| `booking_config.py` | Schedule/private validation and atomic saves |
| `scripts/initialize_booking.ps1` | Copy synthetic private example and create a pause marker for new installations |
| `enable_booking.ps1` | Register or update a **disabled** Windows task |
| `start_booking.ps1` / `stop_booking.ps1` | Explicit enable / indefinite pause |
| `sync_schedule.ps1` | Keep Task Scheduler's trigger aligned with local send time |
| `scripts/install_desktop_launcher.ps1` | Install the Desktop CLI launcher |
| `scheduled_run.cmd` | Actual scheduled sender (not a test command) |
| `tests/` | Unit, synthetic integration, safety and first-run checks |
| `AGENTS.md`, `LESSONS.md`, `CHANGELOG.md`, `MEMORY.md` | Maintainer instructions and project history |

### Local CodeGraph (optional for contributors)

CodeGraph is an optional developer index, not part of the runtime. Run `codegraph status` and `codegraph sync` from the project root if CodeGraph is installed. Its `.codegraph/` database is Git-ignored; **never commit its indexes or private runtime files**.
