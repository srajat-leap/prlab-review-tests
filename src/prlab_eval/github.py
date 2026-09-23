from __future__ import annotations

import json
import subprocess
from typing import Any


class GitHubError(RuntimeError):
    pass


def run(args: list[str], cwd: str | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, check=False, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise GitHubError(f"{' '.join(args)} failed: {detail}")
    return result.stdout


def gh_json(args: list[str]) -> Any:
    return json.loads(run(["gh", *args]) or "null")


def parse_json_pages(raw: str) -> Any:
    """Parse one JSON value, or concatenated arrays from `gh api --paginate`."""
    text = (raw or "").strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        items: list[Any] = []
        idx = 0
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text):
                break
            obj, end = decoder.raw_decode(text, idx)
            if isinstance(obj, list):
                items.extend(obj)
            else:
                items.append(obj)
            idx = end
        return items


def gh_api_list(path: str) -> list[Any]:
    raw = run(["gh", "api", "--paginate", path]) or "[]"
    data = parse_json_pages(raw)
    if data is None:
        return []
    if isinstance(data, list):
        return data
    return [data]
