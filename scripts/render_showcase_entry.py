#!/usr/bin/env python3
"""Render sanitized showcase artifacts from .showcase.json.

Outputs:
- JSON metadata (allowlist only)
- Markdown project card
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

ALLOWED_KEYS = {
    "title",
    "one_liner",
    "problem",
    "solution",
    "impact",
    "stack",
    "status",
    "updated_at",
    "tags",
    "highlights",
    "screenshot_url",
    "demo_url",
    "article_url",
    "visibility_note",
}

REQUIRED_KEYS = {
    "title",
    "one_liner",
    "problem",
    "solution",
    "impact",
    "stack",
}

SENSITIVE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws_secret_access_key"),
    re.compile(r"(?i)api[_-]?key"),
    re.compile(r"(?i)password"),
    re.compile(r"(?i)secret"),
    re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def is_iso_date(value: str) -> bool:
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def walk_strings(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            values.extend(walk_strings(v))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_strings(item))
    return values


def validate(data: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_KEYS - data.keys())
    if missing:
        fail(f"Missing required keys: {', '.join(missing)}")

    for key in REQUIRED_KEYS:
        if key == "stack":
            if not isinstance(data[key], list) or not data[key] or not all(
                isinstance(item, str) and item.strip() for item in data[key]
            ):
                fail("`stack` must be a non-empty list of strings")
            continue
        if not isinstance(data[key], str) or not data[key].strip():
            fail(f"`{key}` must be a non-empty string")

    if "updated_at" in data:
        if not isinstance(data["updated_at"], str) or not is_iso_date(data["updated_at"]):
            fail("`updated_at` must be an ISO date (YYYY-MM-DD)")

    if "tags" in data:
        if not isinstance(data["tags"], list) or not all(isinstance(x, str) for x in data["tags"]):
            fail("`tags` must be a list of strings")

    if "highlights" in data:
        if not isinstance(data["highlights"], list) or not all(
            isinstance(x, str) for x in data["highlights"]
        ):
            fail("`highlights` must be a list of strings")

    all_strings = walk_strings(data)
    for text in all_strings:
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                fail(
                    "Sensitive-looking content detected in metadata. "
                    "Remove secrets from .showcase.json before publishing."
                )


def sanitize(data: dict[str, Any]) -> dict[str, Any]:
    repo = (
        Path(str(data.get("repo", ""))).name
        if data.get("repo")
        else (Path(Path.cwd()).name)
    )
    source_repo = None
    now = dt.datetime.now(dt.UTC)
    now_date = now.date().isoformat()

    env_repo = None
    try:
        import os

        env_repo = os.environ.get("GITHUB_REPOSITORY")
    except Exception:
        env_repo = None

    if env_repo:
        repo = env_repo.split("/")[-1]
        source_repo = env_repo

    out: dict[str, Any] = {k: data[k] for k in ALLOWED_KEYS if k in data}
    out["project_id"] = repo
    out["generated_at"] = now.isoformat().replace("+00:00", "Z")
    out["updated_at"] = out.get("updated_at", now_date)
    if source_repo:
        out["source_repo"] = source_repo
    return out


def render_markdown(data: dict[str, Any]) -> str:
    lines: list[str] = []
    title = data["title"]
    lines.append(f"## {title}")
    lines.append("")
    lines.append(data["one_liner"])
    lines.append("")

    screenshot_url = data.get("screenshot_url")
    if isinstance(screenshot_url, str) and screenshot_url.strip():
        lines.append(f"![{title} screenshot]({screenshot_url})")
        lines.append("")

    lines.append(f"- Status: {data.get('status', 'active')}")
    lines.append(f"- Updated: {data['updated_at']}")
    lines.append(f"- Stack: {', '.join(data['stack'])}")
    lines.append(f"- Impact: {data['impact']}")

    if data.get("demo_url"):
        lines.append(f"- Demo: {data['demo_url']}")
    if data.get("article_url"):
        lines.append(f"- Write-up: {data['article_url']}")
    if data.get("visibility_note"):
        lines.append(f"- Visibility: {data['visibility_note']}")

    if data.get("tags"):
        lines.append(f"- Tags: {', '.join(data['tags'])}")

    lines.append("")
    lines.append("### Problem")
    lines.append("")
    lines.append(data["problem"])
    lines.append("")
    lines.append("### Solution")
    lines.append("")
    lines.append(data["solution"])

    if data.get("highlights"):
        lines.append("")
        lines.append("### Highlights")
        lines.append("")
        for item in data["highlights"][:6]:
            lines.append(f"- {item}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    out_json_path = Path(args.out_json)
    out_md_path = Path(args.out_md)

    if not input_path.exists():
        fail(f"Input file not found: {input_path}")

    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        fail("Input must be a JSON object")

    validate(raw)
    safe = sanitize(raw)

    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)

    out_json_path.write_text(json.dumps(safe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md_path.write_text(render_markdown(safe), encoding="utf-8")


if __name__ == "__main__":
    main()
