#!/usr/bin/env python3
"""Allocate and scaffold the next local Markdown effort Sequence."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / ".scratch"
INDEX = SCRATCH / "README.md"
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ROW_RE = re.compile(r"^\| (\d{3}) \|.*$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="lowercase hyphenated stable slug")
    parser.add_argument("title", help="human-readable effort title")
    parser.add_argument("--blocked-by", default="None.", help="effort dependency text")
    parser.add_argument("--provenance", default="新工作", help="short registry provenance")
    return parser.parse_args()


def safe_table_value(value: str, field: str) -> str:
    if not value.strip() or any(char in value for char in "\n|]"):
        raise SystemExit(f"{field} must be non-empty and cannot contain a newline, | or ]")
    return value.strip()


def main() -> int:
    args = parse_args()
    if not SLUG_RE.fullmatch(args.slug):
        raise SystemExit("slug must contain lowercase letters, digits and single hyphens")
    title = safe_table_value(args.title, "title")
    provenance = safe_table_value(args.provenance, "provenance")
    blocked_by = args.blocked_by.strip()
    if not blocked_by or "\n" in blocked_by:
        raise SystemExit("blocked-by must be non-empty and cannot contain a newline")
    index = INDEX.read_text(encoding="utf-8")
    rows = list(ROW_RE.finditer(index))
    if not rows:
        raise SystemExit(".scratch/README.md does not contain an Effort registry")
    existing = sorted(
        int(match.group(1))
        for path in SCRATCH.iterdir()
        if path.is_dir() and (match := re.fullmatch(r"(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*", path.name))
    )
    sequence = (existing[-1] + 1) if existing else 1
    if sequence > 999:
        raise SystemExit("three-digit effort Sequence space is exhausted")
    sequence_text = f"{sequence:03d}"
    effort = SCRATCH / f"{sequence_text}-{args.slug}"
    effort.mkdir()
    (effort / "issues").mkdir()
    spec = f"""# {title}

Sequence: {sequence_text}

Status: planned
Blocked by: {blocked_by}

## Problem Statement

说明需要解决的问题、受影响的人，以及不解决的后果。

## Solution

说明期望结果和主要约束。

## User Stories

1. 补充第一条可验收的用户故事。

## Implementation Decisions

- 记录已经确定、会约束 tickets 的实现选择。

## Testing Decisions

- 记录必须通过的验证层级和证据要求。

## Out of Scope

列出本 Effort 明确不处理的相邻问题。

## Tickets

创建 ticket 后按不可变 Sequence 顺序链接到这里。

## Further Notes

链接相关 ADR、产品契约、架构视图、前置 ticket 或本 Effort 的 records。
"""
    (effort / "spec.md").write_text(spec, encoding="utf-8")
    insertion = rows[-1].end()
    row = f"\n| {sequence_text} | [{title}]({effort.name}/spec.md) | {provenance} |"
    INDEX.write_text(index[:insertion] + row + index[insertion:], encoding="utf-8")
    print(effort.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
