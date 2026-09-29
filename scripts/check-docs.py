#!/usr/bin/env python3
"""Validate ESPocket Markdown structure and generated architecture diagrams."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "build", "managed_components", "node_modules", "dist"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TERM_RE = re.compile(r"^\*\*(.+?)\*\*[：:]$")
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:")


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if not any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            files.append(path)
    return sorted(files)


def strip_code_fences(text: str) -> str:
    output: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            output.append("")
        else:
            output.append("" if fenced else line)
    return "\n".join(output)


def github_slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[`*_~]", "", value).strip().lower()
    kept = []
    for char in value:
        category = unicodedata.category(char)
        if char in " -_" or category[0] in {"L", "N"}:
            kept.append(char)
    return re.sub(r"[ _]+", "-", "".join(kept)).strip("-")


def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    result: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = github_slug(match.group(2))
        count = seen.get(base, 0)
        seen[base] = count + 1
        result.add(base if count == 0 else f"{base}-{count}")
    return result


def split_destination(raw: str) -> tuple[str, str]:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        value = value[1 : value.index(">")]
    elif " " in value:
        value = value.split(" ", 1)[0]
    value = unquote(value)
    target, marker, fragment = value.partition("#")
    return target, fragment if marker else ""


def check_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    cache: dict[Path, set[str]] = {}
    for source in files:
        text = strip_code_fences(source.read_text(encoding="utf-8"))
        for raw in LINK_RE.findall(text):
            target_text, fragment = split_destination(raw)
            if raw.startswith(EXTERNAL_SCHEMES):
                continue
            target = source if not target_text else (source.parent / target_text).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                errors.append(f"{source.relative_to(ROOT)}: link escapes repo: {raw}")
                continue
            if not target.exists():
                errors.append(f"{source.relative_to(ROOT)}: missing target: {raw}")
                continue
            if fragment and target.is_file() and target.suffix.lower() == ".md":
                available = cache.setdefault(target, anchors(target))
                if fragment.lower() not in available:
                    errors.append(
                        f"{source.relative_to(ROOT)}: missing anchor #{fragment} in {target.relative_to(ROOT)}"
                    )
    return errors


def check_context() -> list[str]:
    path = ROOT / "CONTEXT.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    text = "\n".join(lines)
    if LINK_RE.search(text):
        errors.append("CONTEXT.md: glossary must not contain links")
    forbidden = ("当前实现", "当前固件", "Milestone", "docs/", "firmware/")
    for number, line in enumerate(lines, 1):
        if any(value in line for value in forbidden):
            errors.append(f"CONTEXT.md:{number}: status, path or routing text is not glossary content")
    for index, line in enumerate(lines):
        if not TERM_RE.match(line):
            continue
        definitions: list[str] = []
        cursor = index + 1
        while cursor < len(lines) and lines[cursor].strip() and not lines[cursor].startswith("_Avoid_:"):
            if lines[cursor].startswith("#") or TERM_RE.match(lines[cursor]):
                break
            definitions.append(lines[cursor].strip())
            cursor += 1
        definition = " ".join(definitions)
        if not definition:
            errors.append(f"CONTEXT.md:{index + 1}: term has no definition")
        sentence_count = len(re.findall(r"[。！？.!?](?:\s|$)", definition))
        if sentence_count > 2:
            errors.append(f"CONTEXT.md:{index + 1}: definition exceeds two sentences")
    return errors


def check_scratch() -> list[str]:
    errors: list[str] = []
    scratch = ROOT / ".scratch"
    if not scratch.exists():
        return [".scratch/: local issue tracker is missing"]
    seen_sequences: set[str] = set()
    for effort in sorted(path for path in scratch.iterdir() if path.is_dir()):
        match = re.fullmatch(r"(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*", effort.name)
        if not match:
            errors.append(f"{effort.relative_to(ROOT)}: effort directory must start with an immutable NNN Sequence")
            continue
        sequence = match.group(1)
        if sequence in seen_sequences:
            errors.append(f"{effort.relative_to(ROOT)}: duplicate effort Sequence {sequence}")
        seen_sequences.add(sequence)
        spec = effort / "spec.md"
        if not spec.exists():
            errors.append(f"{effort.relative_to(ROOT)}: missing spec.md")
            continue
        spec_sequence = re.search(r"^Sequence:\s*(\d{3})$", spec.read_text(encoding="utf-8"), re.MULTILINE)
        if not spec_sequence or spec_sequence.group(1) != sequence:
            errors.append(f"{spec.relative_to(ROOT)}: Sequence must match directory prefix {sequence}")
    for spec in scratch.glob("*/spec.md"):
        text = spec.read_text(encoding="utf-8")
        match = re.search(r"^Status:\s*(\S.*)$", text, re.MULTILINE)
        if not match:
            errors.append(f"{spec.relative_to(ROOT)}: missing Status line")
        elif match.group(1).startswith("retrospective") and not re.search(
            r"^Historical basis:\s*\S", text, re.MULTILINE
        ):
            errors.append(f"{spec.relative_to(ROOT)}: retrospective spec lacks Historical basis")
    for issue in scratch.glob("*/issues/*.md"):
        text = issue.read_text(encoding="utf-8")
        if not re.search(r"^\*\*Status:\*\*\s*\S", text, re.MULTILINE):
            errors.append(f"{issue.relative_to(ROOT)}: missing ticket Status")
        if not re.search(r"^\*\*Blocked by:\*\*\s*\S", text, re.MULTILINE):
            errors.append(f"{issue.relative_to(ROOT)}: missing blocking edge")
    return errors


def check_diagrams() -> list[str]:
    errors: list[str] = []
    architecture = ROOT / "docs/design/architecture"
    source_assets = architecture / "assets"
    with tempfile.TemporaryDirectory(prefix="espocket-docs-") as directory:
        temporary = Path(directory) / "architecture"
        shutil.copytree(architecture / "tools", temporary / "tools")
        (temporary / "assets").mkdir()
        generated = subprocess.run(
            ["node", str(temporary / "tools/generate-diagrams.mjs")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if generated.returncode:
            return [f"diagram generation failed: {generated.stderr.strip() or generated.stdout.strip()}"]
        expected = {path.name: path.read_bytes() for path in (temporary / "assets").glob("*.svg")}
        actual = {path.name: path.read_bytes() for path in source_assets.glob("*.svg")}
        if expected.keys() != actual.keys():
            errors.append(
                f"architecture SVG set is stale: expected {sorted(expected)}, found {sorted(actual)}"
            )
        else:
            for name in sorted(expected):
                if expected[name] != actual[name]:
                    errors.append(f"architecture SVG is stale: {name}")
    layout = subprocess.run(
        ["node", str(architecture / "tools/check-diagram-layout.mjs")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if layout.returncode:
        detail = layout.stdout.strip() or layout.stderr.strip()
        errors.append(f"diagram layout check failed:\n{detail}")
    return errors


def main() -> int:
    files = markdown_files()
    errors = check_links(files) + check_context() + check_scratch() + check_diagrams()
    if errors:
        print("documentation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"documentation check passed: {len(files)} Markdown files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
