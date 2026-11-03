from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

from booking_config import (
    ROOT, ConfigError, booking_for_date, compose_message, load_private,
    load_schedule, parse_clock,
)

PROFILE_DIR = ROOT / "chrome_profile"
STATE_FILE = ROOT / "state.json"
AUTH_MARKER = ROOT / "auth.ok"
LOG_FILE = ROOT / "booking.log"
PAUSE_FILE = ROOT / "PAUSED"

TZ = ZoneInfo("Asia/Bangkok")
MAX_LATE_MINUTES = 5


def log(message: str) -> None:
    stamp = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def load_operational_private() -> dict:
    """Reject untouched synthetic onboarding values before any browser/send work."""
    private = load_private()
    if (private["chat_url"].rstrip("/") == "https://www.facebook.com/messages/t/0000000"
            or "000000" in private["student_ids"]):
        raise ConfigError("Replace the example Messenger URL and Student IDs in booking.private.json first.")
    return private


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("Cannot read booking history; send blocked to prevent duplicates.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("last_sent_date"), str):
        raise ConfigError("Booking history is invalid; send blocked to prevent duplicates.")
    return data


def sent_today(day: date) -> bool:
    return load_state().get("last_sent_date") == day.isoformat()


def mark_sent(day: date) -> None:
    # Never persist recipient IDs or the message body in source-controlled files.
    data = {
        "last_sent_date": day.isoformat(),
        "last_sent_at": datetime.now(TZ).isoformat(timespec="seconds"),
    }
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def is_paused() -> bool:
    return PAUSE_FILE.exists()


def find_composer(page, timeout_ms: int = 30000):
    selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
    ]
    deadline = time.time() + timeout_ms / 1000
    last_error = None
    while time.time() < deadline:
        for selector in selectors:
            try:
                items = page.locator(selector)
                for index in range(items.count() - 1, -1, -1):
                    item = items.nth(index)
                    if item.is_visible():
                        return item
            except Exception as exc:
                last_error = exc
        page.wait_for_timeout(500)
    if last_error:
        raise RuntimeError(f"Messenger composer was not found: {last_error}")
    raise RuntimeError("Messenger composer not found. Login may have expired or Facebook changed.")


def open_context(playwright):
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        channel="chrome",
        viewport={"width": 1280, "height": 900},
    )


def get_page(context):
    return context.pages[0] if context.pages else context.new_page()


def authenticate() -> int:
    private = load_operational_private()
    print("Log in manually in the Facebook browser window. Do not enter credentials in this console.")
    print("After the intended booking conversation is visible, return here and press ENTER.")
    with sync_playwright() as playwright:
        context = open_context(playwright)
        try:
            page = get_page(context)
            page.goto(private["chat_url"], wait_until="domcontentloaded", timeout=60000)
            input("\nPress ENTER after Facebook login is complete: ")
            page = context.pages[-1] if context.pages else page
            page.goto(private["chat_url"], wait_until="domcontentloaded", timeout=60000)
            find_composer(page, timeout_ms=30000)
            AUTH_MARKER.write_text(datetime.now(TZ).isoformat(timespec="seconds"), encoding="utf-8")
            print("Facebook Messenger authentication verified and saved locally.")
            return 0
        except Exception as exc:
            print(f"Authentication failed: {type(exc).__name__}")
            return 1
        finally:
            context.close()


def check_auth() -> int:
    private = load_operational_private()
    with sync_playwright() as playwright:
        context = open_context(playwright)
        try:
            page = get_page(context)
            page.goto(private["chat_url"], wait_until="domcontentloaded", timeout=60000)
            find_composer(page, timeout_ms=20000)
            log("Authentication check PASS: Messenger composer is available.")
            return 0
        except Exception as exc:
            log(f"Authentication check FAIL: {type(exc).__name__}")
            return 1
        finally:
            context.close()


def wait_until(target: datetime) -> None:
    while True:
        remaining = (target - datetime.now(TZ)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(3 if remaining > 10 else 0.15 if remaining > 1 else 0.02)


def run_booking() -> int:
    now = datetime.now(TZ)
    day = now.date()
    # Fail closed even for manually launched copies while the Windows task is disabled.
    if is_paused():
        log("Booking automation is paused. Nothing sent.")
        return 0
    try:
        schedule = load_schedule()
        slot = booking_for_date(schedule, day)
        if slot is None:
            log("No booking is scheduled for this date. Exiting.")
            return 0
        if sent_today(day):
            log("Today's booking message was already sent. Exiting.")
            return 0
        if not AUTH_MARKER.exists():
            log("Facebook authentication has not been initialized. Run authentication first.")
            return 2
        private = load_operational_private()
    except ConfigError as exc:
        log(f"Booking configuration invalid: {exc}")
        return 5

    target = datetime.combine(day, parse_clock(schedule["send_time"]), tzinfo=TZ)
    latest = target + timedelta(minutes=MAX_LATE_MINUTES)
    if now > latest:
        log(f"Missed the configured send window by more than {MAX_LATE_MINUTES} minutes. Nothing sent.")
        return 3

    message = compose_message(slot, private)
    log(f"Preparing booking request for {day.isoformat()} (message contents withheld).")
    with sync_playwright() as playwright:
        context = open_context(playwright)
        try:
            page = get_page(context)
            page.goto(private["chat_url"], wait_until="domcontentloaded", timeout=60000)
            composer = find_composer(page, timeout_ms=30000)
            composer.click()
            composer.fill(message)
            log("Messenger composer prepared.")

            if datetime.now(TZ) < target:
                log("Waiting for configured send time.")
                wait_until(target)

            # Recheck local controls at the final send boundary.
            if is_paused():
                log("Pause guard triggered before Enter. Nothing sent.")
                return 0
            if sent_today(day):
                log("Duplicate-send guard triggered before Enter. Nothing sent.")
                return 0
            if load_schedule() != schedule:
                log("Booking settings changed while preparing; stale message not sent.")
                return 0
            if load_operational_private() != private:
                log("Private booking settings changed while preparing; stale message not sent.")
                return 0
            if datetime.now(TZ) > latest:
                log("Send window expired while preparing; nothing sent.")
                return 3

            log("Submitting booking request to Messenger.")
            composer.press("Enter")
            page.wait_for_timeout(2500)
            if (composer.text_content() or "").strip():
                raise RuntimeError("Composer did not clear after submission.")

            mark_sent(day)
            log("Booking message submission confirmed by cleared composer.")
            return 0
        except Exception as exc:
            log(f"Booking automation FAILED: {type(exc).__name__}")
            return 4
        finally:
            context.close()


def validate_installation() -> int:
    """Verify local schedule and personal settings without opening Facebook."""
    load_schedule()
    load_operational_private()
    print("PASS: Schedule and private configuration are valid and no example values remain.")
    return 0


def self_test() -> int:
    # Validate the user's CURRENT settings; customization is expected.
    schedule = load_schedule()
    from booking_config import DAYS
    for index, name in enumerate(DAYS):
        slot = schedule["weekly"][name]
        print(f"PASS {name}: {slot or 'SKIPPED'}")
    print(f"PASS send_time: {schedule['send_time']}")
    print(f"PASS date overrides: {len(schedule['overrides'])}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Badminton Messenger booking automation")
    parser.add_argument("--login", action="store_true", help="Open Facebook for manual login")
    parser.add_argument("--check-auth", action="store_true", help="Verify saved Facebook session")
    parser.add_argument("--self-test", action="store_true", help="Validate current weekly schedule (no Facebook)")
    parser.add_argument("--validate-config", action="store_true", help="Validate schedule and own private settings, without Facebook")
    args = parser.parse_args()
    try:
        if args.login:
            return authenticate()
        if args.check_auth:
            return check_auth()
        if args.self_test:
            return self_test()
        if args.validate_config:
            return validate_installation()
        return run_booking()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
