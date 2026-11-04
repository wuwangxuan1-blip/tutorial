from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".gradle",
    ".kotlin",
    "build",
    "data",
    ".arts",
    ".codeartsdoer",
    "work",
    "node_modules",
}
TEXT_SUFFIXES = {
    ".py",
    ".kt",
    ".kts",
    ".md",
    ".txt",
    ".json",
    ".log",
    ".toml",
    ".properties",
    ".xml",
    ".yml",
    ".yaml",
    ".in",
    ".example",
    ".args",
    ".bat",
    ".sh",
}
PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._\-]{16,}"),
]


def should_scan(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    if path.name == ".env":
        return False
    return path.suffix.lower() in TEXT_SUFFIXES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=str(PROJECT_ROOT / "server" / ".env"))
    args = parser.parse_args()
    load_dotenv(Path(args.env_file), override=False)
    secret = (os.getenv("DEEPSEEK_API_KEY") or "").strip()

    matches: list[dict[str, str]] = []
    scanned = 0
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or not should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        relative = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if secret and secret in text:
            matches.append({"file": relative, "kind": "exact_api_key_value"})
        for pattern in PATTERNS:
            if pattern.search(text):
                matches.append({"file": relative, "kind": "key_pattern"})
                break

    result = {
        "scanned_files": scanned,
        "api_key_configured": bool(secret),
        "matches": matches,
        "clean": not matches,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not matches else 1


if __name__ == "__main__":
    sys.exit(main())