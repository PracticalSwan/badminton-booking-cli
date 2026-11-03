"""Validated local booking schedule and private Messenger settings.

Schedule is source-controlled; recipient and student IDs are intentionally private.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / "schedule.json"
PRIVATE_PATH = ROOT / "booking.private.json"
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
CLOCK = re.compile(r"^[0-2][0-9]:[0-5][0-9]$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ConfigError(ValueError):
    """Invalid or missing booking settings; sending must fail closed."""


def parse_clock(value: str) -> time:
    if not isinstance(value, str) or not CLOCK.fullmatch(value):
        raise ConfigError("Times must use 24-hour HH:MM format.")
    hour, minute = map(int, value.split(":"))
    if hour > 23:
        raise ConfigError("Hour must be between 00 and 23.")
    return time(hour, minute)


def validate_slot(slot: object) -> dict[str, str]:
    if not isinstance(slot, dict) or set(slot) != {"start", "end"}:
        raise ConfigError("A booking must have start and end times.")
    start = parse_clock(slot["start"])
    end = parse_clock(slot["end"])
    if end <= start:
        raise ConfigError("Booking end must be after booking start on the same day.")
    return {"start": slot["start"], "end": slot["end"]}


def validate_schedule(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"version", "send_time", "weekly", "overrides"}:
        raise ConfigError("Schedule must contain version, send_time, weekly, and overrides.")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ConfigError("Unsupported schedule version.")
    send = parse_clock(value["send_time"])
    if send == time(0, 0):
        raise ConfigError("Send time must be between 00:01 and 23:59.")
    weekly = value["weekly"]
    if not isinstance(weekly, dict) or set(weekly) != set(DAYS):
        raise ConfigError("Weekly schedule must contain every weekday, including Saturday and Sunday.")
    clean_weekly = {day: None if weekly[day] is None else validate_slot(weekly[day]) for day in DAYS}
    overrides = value["overrides"]
    if not isinstance(overrides, dict):
        raise ConfigError("Date overrides must be an object.")
    clean_overrides = {}
    for key, slot in overrides.items():
        if not isinstance(key, str) or not DATE.fullmatch(key):
            raise ConfigError("Override dates must use YYYY-MM-DD.")
        try:
            if date.fromisoformat(key).isoformat() != key:
                raise ValueError()
        except ValueError as exc:
            raise ConfigError(f"Invalid override date: {key}") from exc
        clean_overrides[key] = None if slot is None else validate_slot(slot)
    return {"version": 1, "send_time": value["send_time"], "weekly": clean_weekly,
            "overrides": dict(sorted(clean_overrides.items()))}


def load_schedule(path: Path = SCHEDULE_PATH) -> dict:
    try:
        return validate_schedule(json.loads(path.read_text(encoding="utf-8-sig")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot load schedule file: {path.name}") from exc


def save_schedule(config: dict, path: Path = SCHEDULE_PATH) -> None:
    clean = validate_schedule(config)
    data = json.dumps(clean, indent=2, ensure_ascii=False) + "\n"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".schedule-", suffix=".tmp", delete=False) as handle:
            temp_name = handle.name
            handle.write(data)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def booking_for_date(config: dict, day: date) -> dict[str, str] | None:
    key = day.isoformat()
    if key in config["overrides"]:
        return config["overrides"][key]
    return config["weekly"][DAYS[day.weekday()]]


def format_time(value: str) -> str:
    return datetime.combine(date(2000, 1, 1), parse_clock(value)).strftime("%I:%M %p").lstrip("0")


def validate_private(data: object) -> dict:
    """Validate local-only Messenger settings without echoing private values."""
    if not isinstance(data, dict) or set(data) != {"chat_url", "student_ids"}:
        raise ConfigError("Private settings require chat_url and student_ids.")
    url = data["chat_url"]
    if not isinstance(url, str):
        raise ConfigError("Private chat_url must be a Messenger conversation URL.")
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ("www.facebook.com", "facebook.com")
        or not re.fullmatch(r"/messages/t/[0-9]+/?", parsed.path)
        or parsed.query or parsed.fragment or parsed.username or parsed.password
    ):
        raise ConfigError("Private chat_url must be a direct HTTPS Facebook Messenger conversation URL.")
    ids = data["student_ids"]
    if (
        not isinstance(ids, list)
        or not ids
        or any(not isinstance(item, str) or not re.fullmatch(r"[0-9]{1,16}", item) for item in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ConfigError("Student IDs must be a nonempty list of unique numeric strings (up to 16 digits).")
    return {"chat_url": url, "student_ids": list(ids)}


def is_example_private(data: dict) -> bool:
    """Identify synthetic onboarding values that must never be used for booking."""
    return (data["chat_url"].rstrip("/") == "https://www.facebook.com/messages/t/0000000"
            or "000000" in data["student_ids"])


def load_private(path: Path = PRIVATE_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("Private booking settings are missing or invalid. See README.md.") from exc
    return validate_private(data)


def save_private(data: dict, path: Path = PRIVATE_PATH) -> None:
    """Atomically persist local identity settings, with no plaintext backup."""
    clean = validate_private(data)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".booking-private-", suffix=".tmp", delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(clean, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def compose_message(slot: dict[str, str], private: dict) -> str:
    return f"Booking Badminton Court  {format_time(slot['start'])} to {format_time(slot['end'])}  {' '.join(private['student_ids'])}"
