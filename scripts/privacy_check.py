"""Fail CI/push if private runtime files or identity values were staged."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLOCKED = (
    "booking.private.json", "auth.ok", "state.json", "PAUSED",
    "booking.log", "task_console.log", "browser_profile/", "chrome_profile/",
    ".venv/", ".ai-bridge/", "__pycache__/",
)
SUSPECT = (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
           re.compile(r"(?i)(?:gho_|ghp_|github_pat_|sk-proj-)[A-Za-z0-9_-]{8,}"))
IDENTIFIER = re.compile(r"(?<![0-9])[0-9]{7,16}(?![0-9])")


def main() -> int:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    paths = [x.decode("utf-8") for x in result.stdout.split(b"\0") if x]
    errors = []
    if not paths:
        errors.append("No Git-tracked files available for privacy audit.")
    private = ROOT / "booking.private.json"
    sensitive = []
    if private.exists():
        data = json.loads(private.read_text(encoding="utf-8-sig"))
        sensitive.extend(data.get("student_ids", []))
        sensitive.append(data.get("chat_url", ""))
        # Extract messenger recipient ID as well, not only full URL.
        sensitive.append(data.get("chat_url", "").rstrip("/").split("/")[-1])
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized in BLOCKED or any(normalized.startswith(prefix) for prefix in BLOCKED if prefix.endswith("/")):
            errors.append(f"Forbidden tracked path: {normalized}")
            continue
        # Audit the exact staged Git blob, not the potentially different worktree file.
        try:
            blob = subprocess.run(["git", "show", ":" + normalized], cwd=ROOT,
                                  check=True, capture_output=True).stdout
            content = blob.decode("utf-8")
        except (UnicodeError, OSError, subprocess.CalledProcessError):
            errors.append(f"Unreadable/binary staged file: {normalized}")
            continue
        for marker in sensitive:
            if marker and marker in content:
                errors.append(f"Private identity value found in: {normalized}")
                break
        if any(pattern.search(content) for pattern in SUSPECT):
            errors.append(f"Possible credential in: {normalized}")
        if any(set(m.group()) != {"0"} for m in IDENTIFIER.finditer(content)):
            errors.append(f"Possible student or conversation numeric identifier in: {normalized}")
    if errors:
        print("PRIVACY CHECK FAILED:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    print(f"Privacy gate PASS: inspected {len(paths)} tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
