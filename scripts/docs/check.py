#!/usr/bin/env python3
"""Validate ESPocket Markdown structure and generated architecture diagrams."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
SKIP_PARTS = {".git", "build", "managed_components", "node_modules", "dist"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TERM_RE = re.compile(r"^\*\*(.+?)\*\*[：:]$")
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:")
EFFORT_STATUSES = {
    "planned",
    "active",
    "blocked",
    "resolved",
    "retrospective-active",
    "retrospective-resolved",
}
TICKET_STATUSES = {
    "needs-triage",
    "needs-info",
    "ready-for-agent",
    "ready-for-human",
    "wontfix",
    "resolved",
    "retrospective-resolved",
}


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


def check_discoverability(files: list[Path]) -> list[str]:
    """Require every Markdown document except the repository entrypoint to have an inbound link."""
    inbound = {path.resolve(): 0 for path in files}
    for source in files:
        text = strip_code_fences(source.read_text(encoding="utf-8"))
        for raw in LINK_RE.findall(text):
            target_text, _ = split_destination(raw)
            if not target_text or raw.startswith(EXTERNAL_SCHEMES):
                continue
            target = (source.parent / target_text).resolve()
            if target.is_dir() and (target / "README.md").exists():
                target = (target / "README.md").resolve()
            if target in inbound:
                inbound[target] += 1
    allowed_roots = {(ROOT / "README.md").resolve()}
    return [
        f"{path.relative_to(ROOT)}: Markdown document is not reachable from another document"
        for path, count in sorted(inbound.items())
        if count == 0 and path not in allowed_roots
    ]


def check_raw_artifacts() -> list[str]:
    errors: list[str] = []
    milestones = ROOT / "docs/milestones"
    evidence_root = ROOT / "evidence"
    if evidence_root.exists():
        errors.append("evidence/: raw acceptance artifacts must not be committed to the source tree")
    docs_root = ROOT / "docs"
    for legacy in sorted(
        path for path in docs_root.rglob("*")
        if path.is_dir() and path.name in {"evidence", "shared-evidence", "verification"}
    ):
        errors.append(f"{legacy.relative_to(ROOT)}/: raw artifacts and shared verification docs do not belong under docs/")
    for path in milestones.rglob("*"):
        if not path.is_file() or path.suffix.lower() == ".md":
            continue
        errors.append(f"{path.relative_to(ROOT)}: raw Milestone artifacts must not be committed under docs/")
    return errors


def check_authority_layout() -> list[str]:
    errors: list[str] = []
    if (ROOT / "docs/guides").exists():
        errors.append("docs/guides/: firmware operations belong in firmware/README.md")
    if not (ROOT / "firmware/README.md").exists():
        errors.append("firmware/README.md: missing firmware-local build instructions")
    return errors


def check_product_docs() -> list[str]:
    errors: list[str] = []
    directory = ROOT / "docs/design/product"
    index_path = directory / "README.md"
    if not index_path.exists():
        return ["docs/design/product/README.md: missing product index"]

    numbered = sorted(path for path in directory.glob("*.md") if path.name != "README.md")
    sequences: list[int] = []
    requirement_owners: dict[str, Path] = {}
    required_headings = ("目的", "用户结果", "产品要求", "非目标")
    forbidden = ("Milestone", "ADR", ".scratch", "firmware/", "docs/", "evidence/", "当前实现", "当前状态", "源码")

    for path in numbered:
        match = re.fullmatch(r"(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md", path.name)
        if not match:
            errors.append(f"{path.relative_to(ROOT)}: product filename must start with a contiguous NN Sequence")
            continue
        sequence = int(match.group(1))
        sequences.append(sequence)
        text = path.read_text(encoding="utf-8")
        if not re.search(rf"^# {sequence:02d}\s+[—-]\s+\S", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: title must match product Sequence {sequence:02d}")
        expected_headings = ["目的", "用户结果", "产品要求"]
        if sequence != 2:
            expected_headings.append("AI Native")
        expected_headings.append("非目标")
        positions: list[int] = []
        for heading in required_headings:
            if not re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE):
                errors.append(f"{path.relative_to(ROOT)}: missing ## {heading}")
        for heading in expected_headings:
            heading_match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
            if heading_match:
                positions.append(heading_match.start())
        if positions != sorted(positions):
            errors.append(f"{path.relative_to(ROOT)}: product sections are out of canonical order")
        has_ai_section = bool(re.search(r"^## AI Native\s*$", text, re.MULTILINE))
        if sequence == 2 and has_ai_section:
            errors.append(f"{path.relative_to(ROOT)}: AI Native document must not nest a duplicate AI Native section")
        if sequence != 2 and not has_ai_section:
            errors.append(f"{path.relative_to(ROOT)}: missing ## AI Native")
        for term in forbidden:
            if term in text:
                errors.append(f"{path.relative_to(ROOT)}: product requirements contain non-product reference {term!r}")

        identifiers = re.findall(r"^\|\s*([A-Z]+-\d{3})\s*\|", text, re.MULTILINE)
        if not identifiers:
            errors.append(f"{path.relative_to(ROOT)}: missing stable Requirement IDs")
        for identifier in identifiers:
            if identifier in requirement_owners:
                errors.append(
                    f"{path.relative_to(ROOT)}: Requirement ID {identifier} duplicates "
                    f"{requirement_owners[identifier].relative_to(ROOT)}"
                )
            else:
                requirement_owners[identifier] = path
        ai_section = re.search(r"^## AI Native\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
        if ai_section and not re.search(r"^\|\s*[A-Z]+-\d{3}\s*\|", ai_section.group(1), re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: AI Native section needs explicit Requirement IDs")

    if sequences and sequences != list(range(1, len(sequences) + 1)):
        errors.append(
            "docs/design/product/: product Sequence must be contiguous from 01; "
            f"found {', '.join(f'{value:02d}' for value in sequences)}"
        )

    index = index_path.read_text(encoding="utf-8")
    linked = re.findall(r"\]\(((?:\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md)\)", index)
    names = [path.name for path in numbered]
    if linked != names:
        errors.append("docs/design/product/README.md: product index must list every numbered document exactly once in Sequence order")

    for path in [index_path, *numbered]:
        text = strip_code_fences(path.read_text(encoding="utf-8"))
        for raw in LINK_RE.findall(text):
            target_text, _ = split_destination(raw)
            if not target_text or raw.startswith(EXTERNAL_SCHEMES):
                continue
            target = (path.parent / target_text).resolve()
            try:
                target.relative_to(directory.resolve())
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: product docs may link only within the product directory: {raw}")
    return errors


def check_architecture_docs() -> list[str]:
    errors: list[str] = []
    directory = ROOT / "docs/design/architecture"
    index_path = directory / "README.md"
    if not index_path.exists():
        return ["docs/design/architecture/README.md: missing architecture index"]

    product_ids: set[str] = set()
    for path in (ROOT / "docs/design/product").glob("[0-9][0-9]-*.md"):
        product_ids.update(re.findall(r"^\|\s*([A-Z]+-\d{3})\s*\|", path.read_text(encoding="utf-8"), re.MULTILINE))

    numbered = sorted(path for path in directory.glob("*.md") if path.name != "README.md")
    sequences: list[int] = []
    invariant_owners: dict[str, Path] = {}
    required_headings = ("目的", "支撑的产品要求", "结构", "架构不变量", "AI Native", "Code Anchors", "非目标")
    forbidden = ("Milestone", ".scratch", "BLOCKED", "NOT TESTED", "实施状态", "当前实现", "当前固件")

    for path in numbered:
        match = re.fullmatch(r"(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md", path.name)
        if not match:
            errors.append(f"{path.relative_to(ROOT)}: architecture filename must start with a contiguous NN Sequence")
            continue
        sequence = int(match.group(1))
        sequences.append(sequence)
        text = path.read_text(encoding="utf-8")
        if not re.search(rf"^# {sequence:02d}\s+[—-]\s+\S", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: title must match architecture Sequence {sequence:02d}")
        positions: list[int] = []
        for heading in required_headings:
            heading_match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
            if not heading_match:
                errors.append(f"{path.relative_to(ROOT)}: missing ## {heading}")
            else:
                positions.append(heading_match.start())
        if positions != sorted(positions):
            errors.append(f"{path.relative_to(ROOT)}: architecture sections are out of canonical order")
        for term in forbidden:
            if term in text:
                errors.append(f"{path.relative_to(ROOT)}: architecture contains status or work reference {term!r}")
        if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text):
            errors.append(f"{path.relative_to(ROOT)}: architecture must not contain dated status")
        if not re.search(r"!\[[^\]]+\]\(assets/[a-z0-9-]+\.svg\)", text):
            errors.append(f"{path.relative_to(ROOT)}: architecture view must include a generated SVG")

        mapping_section = re.search(
            r"^## 支撑的产品要求\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE
        )
        mapped_ids = set(re.findall(r"\b[A-Z]+-\d{3}\b", mapping_section.group(1) if mapping_section else ""))
        if not mapped_ids:
            errors.append(f"{path.relative_to(ROOT)}: missing Product Requirement mapping")
        for identifier in sorted(mapped_ids - product_ids):
            errors.append(f"{path.relative_to(ROOT)}: unknown Product Requirement ID {identifier}")

        invariant_section = re.search(r"^## 架构不变量\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
        identifiers = re.findall(
            r"^\|\s*([A-Z]{3}-\d{3})\s*\|",
            invariant_section.group(1) if invariant_section else "",
            re.MULTILINE,
        )
        if not identifiers:
            errors.append(f"{path.relative_to(ROOT)}: missing stable Architecture Invariant IDs")
        for identifier in identifiers:
            if identifier in invariant_owners:
                errors.append(
                    f"{path.relative_to(ROOT)}: Architecture Invariant ID {identifier} duplicates "
                    f"{invariant_owners[identifier].relative_to(ROOT)}"
                )
            else:
                invariant_owners[identifier] = path

        ai_section = re.search(r"^## AI Native\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
        if ai_section and "Exposure Decision" not in ai_section.group(1):
            errors.append(f"{path.relative_to(ROOT)}: AI Native section must state an Exposure Decision")

        code_section = re.search(r"^## Code Anchors\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
        code_links = LINK_RE.findall(code_section.group(1) if code_section else "")
        if not code_links:
            errors.append(f"{path.relative_to(ROOT)}: Code Anchors must link to at least one implementation seam")
        for raw in code_links:
            target_text, _ = split_destination(raw)
            if not target_text or raw.startswith(EXTERNAL_SCHEMES):
                continue
            target = (path.parent / target_text).resolve()
            try:
                target.relative_to((ROOT / "firmware").resolve())
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: Code Anchor must point inside firmware/: {raw}")

    if sequences and sequences != list(range(1, len(sequences) + 1)):
        errors.append(
            "docs/design/architecture/: architecture Sequence must be contiguous from 01; "
            f"found {', '.join(f'{value:02d}' for value in sequences)}"
        )

    index = index_path.read_text(encoding="utf-8")
    for term in forbidden:
        if term in index:
            errors.append(f"docs/design/architecture/README.md: architecture index contains status or work reference {term!r}")
    linked = re.findall(r"\]\(((?:\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md)\)", index)
    names = [path.name for path in numbered]
    if linked != names:
        errors.append(
            "docs/design/architecture/README.md: architecture index must list every numbered document exactly once in Sequence order"
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


def check_adrs() -> list[str]:
    errors: list[str] = []
    directory = ROOT / "docs/adr"
    records = sorted(path for path in directory.glob("*.md") if path.name != "README.md")
    seen: set[str] = set()
    for path in records:
        match = re.fullmatch(r"(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md", path.name)
        if not match:
            errors.append(f"{path.relative_to(ROOT)}: ADR filename must start with an immutable NNNN Sequence")
            continue
        sequence = match.group(1)
        seen.add(sequence)
        text = path.read_text(encoding="utf-8")
        if not re.search(rf"^# ADR-{sequence}:\s+\S", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: title must match ADR Sequence {sequence}")
        if not re.search(r"^- Status:\s*`(?:proposed|accepted|deprecated|superseded)`$", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: missing or invalid ADR Status")
        if not re.search(r"^- Recorded:\s*\d{4}-\d{2}-\d{2}$", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: missing Recorded date")
        if not re.search(r"^- Origin:\s*\S", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: missing decision Origin")
    if seen:
        maximum = max(int(value) for value in seen)
        expected = {f"{value:04d}" for value in range(1, maximum + 1)}
        if seen != expected:
            errors.append(f"docs/adr/: missing immutable ADR Sequence(s): {', '.join(sorted(expected - seen))}")
    index = (directory / "README.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\(((?:\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md)\)", index))
    names = {path.name for path in records}
    if linked != names:
        if missing := sorted(names - linked):
            errors.append(f"docs/adr/README.md: unindexed ADR(s): {', '.join(missing)}")
        if stale := sorted(linked - names):
            errors.append(f"docs/adr/README.md: stale ADR link(s): {', '.join(stale)}")
    return errors


def check_scratch() -> list[str]:
    errors: list[str] = []
    scratch = ROOT / ".scratch"
    if not scratch.exists():
        return [".scratch/: local issue tracker is missing"]
    seen_sequences: set[str] = set()
    efforts = sorted(path for path in scratch.iterdir() if path.is_dir())
    effort_names: set[str] = set()
    for effort in efforts:
        match = re.fullmatch(r"(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*", effort.name)
        if not match:
            errors.append(f"{effort.relative_to(ROOT)}: effort directory must start with an immutable NNN Sequence")
            continue
        sequence = match.group(1)
        effort_names.add(effort.name)
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
    if seen_sequences:
        maximum = max(int(value) for value in seen_sequences)
        expected_sequences = {f"{value:03d}" for value in range(1, maximum + 1)}
        if seen_sequences != expected_sequences:
            missing = sorted(expected_sequences - seen_sequences)
            errors.append(f".scratch/: missing immutable effort Sequence(s): {', '.join(missing)}")
    index_text = (scratch / "README.md").read_text(encoding="utf-8")
    indexed_efforts = set(re.findall(r"\]\(((?:\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*)/spec\.md\)", index_text))
    if indexed_efforts != effort_names:
        missing = sorted(effort_names - indexed_efforts)
        stale = sorted(indexed_efforts - effort_names)
        if missing:
            errors.append(f".scratch/README.md: unindexed effort(s): {', '.join(missing)}")
        if stale:
            errors.append(f".scratch/README.md: stale effort link(s): {', '.join(stale)}")
    for spec in scratch.glob("*/spec.md"):
        text = spec.read_text(encoding="utf-8")
        match = re.search(r"^Status:\s*(\S.*)$", text, re.MULTILINE)
        if not match:
            errors.append(f"{spec.relative_to(ROOT)}: missing Status line")
        elif match.group(1) not in EFFORT_STATUSES:
            errors.append(f"{spec.relative_to(ROOT)}: invalid effort Status {match.group(1)!r}")
        elif match.group(1).startswith("retrospective") and not re.search(
            r"^Historical basis:\s*\S", text, re.MULTILINE
        ):
            errors.append(f"{spec.relative_to(ROOT)}: retrospective spec lacks Historical basis")
        if not re.search(r"^Blocked by:\s*\S", text, re.MULTILINE):
            errors.append(f"{spec.relative_to(ROOT)}: missing Blocked by line")
    for effort in efforts:
        seen_issue_sequences: set[str] = set()
        issue_files = sorted((effort / "issues").glob("*.md"))
        for issue in issue_files:
            name_match = re.fullmatch(r"(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md", issue.name)
            if not name_match:
                errors.append(f"{issue.relative_to(ROOT)}: ticket filename must start with an immutable NN Sequence")
                continue
            issue_sequence = name_match.group(1)
            if issue_sequence in seen_issue_sequences:
                errors.append(f"{issue.relative_to(ROOT)}: duplicate ticket Sequence {issue_sequence}")
            seen_issue_sequences.add(issue_sequence)
            text = issue.read_text(encoding="utf-8")
            if not re.search(rf"^# {issue_sequence}\s+[—-]\s+\S", text, re.MULTILINE):
                errors.append(f"{issue.relative_to(ROOT)}: title must match ticket Sequence {issue_sequence}")
            status = re.search(r"^\*\*Status:\*\*\s*(\S.*)$", text, re.MULTILINE)
            if not status:
                errors.append(f"{issue.relative_to(ROOT)}: missing ticket Status")
            elif status.group(1) not in TICKET_STATUSES:
                errors.append(f"{issue.relative_to(ROOT)}: invalid ticket Status {status.group(1)!r}")
            if not re.search(r"^\*\*Blocked by:\*\*\s*\S", text, re.MULTILINE):
                errors.append(f"{issue.relative_to(ROOT)}: missing blocking edge")
            if not re.search(r"^- \[[ x]\]\s+\S", text, re.MULTILINE):
                errors.append(f"{issue.relative_to(ROOT)}: missing acceptance checklist")
            if status and status.group(1) in {"resolved", "retrospective-resolved"} and not re.search(
                r"^## Resolution\s*$", text, re.MULTILINE
            ):
                errors.append(f"{issue.relative_to(ROOT)}: resolved ticket lacks Resolution")
        linked_issues = set(
            re.findall(
                r"\]\(issues/((?:\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md)\)",
                (effort / "spec.md").read_text(encoding="utf-8"),
            )
        )
        issue_names = {path.name for path in issue_files}
        if linked_issues != issue_names:
            missing = sorted(issue_names - linked_issues)
            stale = sorted(linked_issues - issue_names)
            if missing:
                errors.append(f"{(effort / 'spec.md').relative_to(ROOT)}: unlinked ticket(s): {', '.join(missing)}")
            if stale:
                errors.append(f"{(effort / 'spec.md').relative_to(ROOT)}: stale ticket link(s): {', '.join(stale)}")
    return errors


def check_diagrams() -> list[str]:
    errors: list[str] = []
    architecture = ROOT / "docs/design/architecture"
    source_assets = architecture / "assets"
    with tempfile.TemporaryDirectory(prefix="espocket-docs-") as directory:
        temporary_assets = Path(directory) / "assets"
        generated = subprocess.run(
            ["node", str(SCRIPT_DIR / "generate-architecture-diagrams.mjs"), str(temporary_assets)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=os.environ.copy(),
        )
        if generated.returncode:
            return [f"diagram generation failed: {generated.stderr.strip() or generated.stdout.strip()}"]
        expected = {path.name: path.read_bytes() for path in temporary_assets.glob("*.svg")}
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
        ["node", str(SCRIPT_DIR / "check-architecture-diagram-layout.mjs")],
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
    errors = (
        check_links(files)
        + check_discoverability(files)
        + check_context()
        + check_product_docs()
        + check_architecture_docs()
        + check_adrs()
        + check_scratch()
        + check_raw_artifacts()
        + check_authority_layout()
        + check_diagrams()
    )
    if errors:
        print("documentation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"documentation check passed: {len(files)} Markdown files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
