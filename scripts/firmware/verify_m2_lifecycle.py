#!/usr/bin/env python3
"""Validate ESPocket M2 lifecycle stress markers from serial output or a saved log."""

from __future__ import annotations

import argparse
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path


ANSI_ESCAPE = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")
LOG_PREFIX = rb"(?:[EWIDV] \(\d+\) [^:\n]+: )?"
CYCLE_PATTERN = re.compile(
    rb"^" + LOG_PREFIX +
    rb"M2_STRESS CYCLE cycle=(\d+) start=Running stop=Stopped gui=Unloaded "
    rb"internal_free=(\d+) psram_free=(\d+) "
    rb"internal_largest=(\d+) psram_largest=(\d+)[ \t]*$",
    re.MULTILINE,
)
FAILURE_PATTERN = re.compile(
    rb"M2_STRESS FAIL|Guru Meditation|panic(?:ed)?|assert failed|abort\(\)|"
    rb"Stack smashing|CORRUPT HEAP|Task watchdog got triggered|"
    rb"Interrupt wdt timeout on CPU|\brst:0x[0-9a-f]+\b|"
    rb"Failed to (?:post app GUI cleanup task|cleanup app GUI while stopping app|unload app GUI document)",
    re.IGNORECASE,
)
BEGIN_MARKER = b"M2_STRESS BEGIN cycles=50"
COMPLETE_MARKER = b"M2_STRESS COMPLETE cycles=50"
STARTED_MARKER = b"ESPocket started"
BEGIN_PATTERN = re.compile(
    rb"^" + LOG_PREFIX + rb"M2_STRESS BEGIN cycles=50 app_id=\d+[ \t]*$",
    re.MULTILINE,
)
COMPLETE_PATTERN = re.compile(
    rb"^" + LOG_PREFIX + rb"M2_STRESS COMPLETE cycles=50[ \t]*$",
    re.MULTILINE,
)
STARTED_PATTERN = re.compile(
    rb"^" + LOG_PREFIX + rb"ESPocket started[ \t]*$",
    re.MULTILINE,
)
PROTOCOL_PATTERNS = (
    (
        "begin",
        re.compile(rb"^" + LOG_PREFIX + rb"M2_STRESS BEGIN\b[^\n]*$", re.MULTILINE),
        BEGIN_PATTERN,
    ),
    (
        "cycle",
        re.compile(rb"^" + LOG_PREFIX + rb"M2_STRESS CYCLE\b[^\n]*$", re.MULTILINE),
        CYCLE_PATTERN,
    ),
    (
        "completion",
        re.compile(rb"^" + LOG_PREFIX + rb"M2_STRESS COMPLETE\b[^\n]*$", re.MULTILINE),
        COMPLETE_PATTERN,
    ),
    (
        "startup",
        re.compile(rb"^" + LOG_PREFIX + rb"ESPocket started\S*[^\n]*$", re.MULTILINE),
        STARTED_PATTERN,
    ),
)
METRICS = ("internal_free", "psram_free", "internal_largest", "psram_largest")
EXPECTED_CYCLES = 50
MAX_MEDIAN_LOSS = 1024
DECREASING_WINDOW = 5


@dataclass(frozen=True)
class Sample:
    cycle: int
    internal_free: int
    psram_free: int
    internal_largest: int
    psram_largest: int


def clean_log(data: bytes) -> bytes:
    return ANSI_ESCAPE.sub(b"", data).replace(b"\r", b"")


def find_malformed_protocol_records(data: bytes) -> list[tuple[int, str, bytes]]:
    malformed: list[tuple[int, str, bytes]] = []
    for name, candidate_pattern, exact_pattern in PROTOCOL_PATTERNS:
        for match in candidate_pattern.finditer(data):
            if exact_pattern.fullmatch(match.group(0)) is None:
                malformed.append((match.start(), name, match.group(0)))
    return sorted(malformed)


def parse_samples(data: bytes) -> tuple[list[Sample], list[str]]:
    samples: list[Sample] = []
    seen: set[int] = set()
    errors: list[str] = []
    for match in CYCLE_PATTERN.finditer(data):
        values = [int(value) for value in match.groups()]
        sample = Sample(*values)
        if sample.cycle in seen:
            errors.append(f"duplicate cycle {sample.cycle}")
            continue
        seen.add(sample.cycle)
        samples.append(sample)
    return samples, errors


def evaluate(data: bytes) -> tuple[list[str], dict[str, tuple[int, int, int]]]:
    data = clean_log(data)
    errors: list[str] = []

    for _, name, record in find_malformed_protocol_records(data):
        errors.append(
            f"malformed {name} record: {record.decode(errors='replace')}"
        )

    begin_matches = list(BEGIN_PATTERN.finditer(data))
    complete_matches = list(COMPLETE_PATTERN.finditer(data))
    started_matches = list(STARTED_PATTERN.finditer(data))
    begin_offsets = [match.start() for match in begin_matches]
    complete_offsets = [match.start() for match in complete_matches]
    started_offsets = [match.start() for match in started_matches]
    if len(begin_offsets) != 1:
        errors.append(f"expected exactly one begin marker, found {len(begin_offsets)}")
    if len(complete_offsets) != 1:
        errors.append(f"expected exactly one completion marker, found {len(complete_offsets)}")
    if len(started_offsets) != 1:
        errors.append(f"expected exactly one ESPocket startup marker, found {len(started_offsets)}")

    run_data = data
    if len(begin_offsets) == len(complete_offsets) == len(started_offsets) == 1:
        begin_offset = begin_offsets[0]
        complete_offset = complete_offsets[0]
        started_offset = started_offsets[0]
        if not begin_offset < complete_offset < started_offset:
            errors.append("begin, completion, and startup markers are out of order")
        else:
            run_data = data[begin_offset:started_matches[0].end()]
            if len(CYCLE_PATTERN.findall(data)) != len(CYCLE_PATTERN.findall(run_data)):
                errors.append("cycle markers exist outside the unique run boundary")

    samples, sample_errors = parse_samples(run_data)
    errors.extend(sample_errors)
    failure = FAILURE_PATTERN.search(run_data)
    if failure:
        errors.append(f"failure signature: {failure.group(0).decode(errors='replace')}")

    if len(begin_offsets) == len(complete_offsets) == len(started_offsets) == 1:
        begin = BEGIN_PATTERN.search(run_data)
        complete = COMPLETE_PATTERN.search(run_data)
        cycle_matches = list(CYCLE_PATTERN.finditer(run_data))
        if samples and (
            begin is None or complete is None or not cycle_matches or
            not begin.start() < cycle_matches[0].start() or
            cycle_matches[-1].start() >= complete.start()
        ):
            errors.append("cycle markers are outside the begin/complete boundary")

    cycles = [sample.cycle for sample in samples]
    expected = list(range(1, EXPECTED_CYCLES + 1))
    if cycles != expected:
        missing = sorted(set(expected) - set(cycles))
        unexpected = sorted(set(cycles) - set(expected))
        errors.append(f"cycle sequence mismatch: missing={missing}, unexpected={unexpected}")

    medians: dict[str, tuple[int, int, int]] = {}
    if cycles == expected:
        for sample in samples:
            for metric in METRICS:
                if getattr(sample, metric) <= 0:
                    errors.append(f"{metric} is zero at cycle {sample.cycle}")

        measured_samples = samples[1:]
        for metric in METRICS:
            early = int(statistics.median(getattr(sample, metric) for sample in samples[1:6]))
            late = int(statistics.median(getattr(sample, metric) for sample in samples[45:50]))
            loss = max(0, early - late)
            medians[metric] = (early, late, loss)
            if loss > MAX_MEDIAN_LOSS:
                errors.append(f"{metric} median loss {loss} exceeds {MAX_MEDIAN_LOSS} bytes")

            decrease_streak = 0
            for previous, current in zip(measured_samples, measured_samples[1:]):
                if getattr(current, metric) < getattr(previous, metric):
                    decrease_streak += 1
                    if decrease_streak >= DECREASING_WINDOW - 1:
                        errors.append(f"{metric} decreases across {DECREASING_WINDOW} consecutive samples")
                        break
                else:
                    decrease_streak = 0

    return errors, medians


def capture_should_stop(data: bytes) -> bool:
    data = clean_log(data)
    last_newline = data.rfind(b"\n")
    if last_newline < 0:
        return False
    data = data[:last_newline + 1]

    begin_matches = list(BEGIN_PATTERN.finditer(data))
    if len(begin_matches) > 1:
        return True
    if len(begin_matches) != 1:
        return False

    run_data = data[begin_matches[0].start():]
    if find_malformed_protocol_records(run_data) or FAILURE_PATTERN.search(run_data):
        return True
    complete = COMPLETE_PATTERN.search(run_data)
    started = STARTED_PATTERN.search(run_data)
    return complete is not None and started is not None and complete.start() < started.start()


def capture_serial(port: str, timeout: float) -> bytes:
    import serial

    deadline = time.monotonic() + timeout
    captured = bytearray()
    monitor = None
    try:
        while time.monotonic() < deadline:
            if monitor is None:
                try:
                    monitor = serial.Serial(port, 115200, timeout=0.1)
                except (OSError, serial.SerialException):
                    time.sleep(0.1)
                    continue

            try:
                chunk = monitor.read(monitor.in_waiting or 1)
            except (OSError, serial.SerialException):
                monitor.close()
                monitor = None
                time.sleep(0.1)
                continue
            if not chunk:
                continue

            captured.extend(chunk)
            if capture_should_stop(bytes(captured)):
                break
    finally:
        if monitor is not None:
            monitor.close()
    return bytes(captured)


def run_self_test() -> None:
    def require(condition: bool, message: object) -> None:
        if not condition:
            raise RuntimeError(f"M2 lifecycle parser self-test failed: {message}")

    def make_log(overrides: dict[int, dict[str, int]] | None = None) -> bytes:
        overrides = overrides or {}
        lines = []
        for cycle in range(1, EXPECTED_CYCLES + 1):
            values = {
                "internal_free": 100000,
                "psram_free": 4500000,
                "internal_largest": 32000,
                "psram_largest": 4400000,
            }
            values.update(overrides.get(cycle, {}))
            lines.append(
                f"M2_STRESS CYCLE cycle={cycle} start=Running stop=Stopped gui=Unloaded "
                f"internal_free={values['internal_free']} psram_free={values['psram_free']} "
                f"internal_largest={values['internal_largest']} psram_largest={values['psram_largest']}"
            )
        return (
            "M2_STRESS BEGIN cycles=50 app_id=2\n"
            + "\n".join(lines)
            + "\nM2_STRESS COMPLETE cycles=50\nESPocket started\n"
        ).encode()

    valid = make_log()
    errors, medians = evaluate(valid)
    require(not errors, errors)
    require(
        all(early == late and loss == 0 for early, late, loss in medians.values()),
        medians,
    )

    prefixed = b"".join(
        b"I (123) ESPocket.System: " + line + b"\n"
        for line in valid.splitlines()
    )
    errors, _ = evaluate(prefixed)
    require(not errors, errors)

    for malformed in (
        valid.replace(b"M2_STRESS COMPLETE cycles=50", b"M2_STRESS COMPLETE cycles=500"),
        valid.replace(b"ESPocket started", b"ESPocket startedness"),
        valid.replace(b"internal_largest=32000 psram_largest=4400000", b"internal_largest=32000 psram_largest=4400000 trailing", 1),
    ):
        errors, _ = evaluate(malformed)
        require(bool(errors), "malformed protocol record was accepted")

    stale_prefix = b"Guru Meditation from an earlier capture\n"
    begin_only = b"M2_STRESS BEGIN cycles=50 app_id=2\n"
    require(not capture_should_stop(stale_prefix + begin_only), "pre-run failure stopped live capture")
    require(capture_should_stop(begin_only + b"Guru Meditation\n"), "in-run failure did not stop live capture")
    require(capture_should_stop(stale_prefix + valid), "complete run did not stop live capture")

    explicit_failure = valid.replace(COMPLETE_MARKER, b"M2_STRESS FAIL cycle=1 phase=self_test")
    errors, _ = evaluate(explicit_failure)
    require(any("failure signature" in error for error in errors), errors)

    median_leak = make_log({cycle: {"internal_free": 97952} for cycle in range(46, 51)})
    errors, _ = evaluate(median_leak)
    require(any("internal_free median loss 2048" in error for error in errors), errors)

    descending = make_log({cycle: {"internal_largest": 33000 - cycle} for cycle in range(2, 7)})
    errors, _ = evaluate(descending)
    require(any("internal_largest decreases across 5 consecutive samples" in error for error in errors), errors)

    zero_metric = make_log({25: {"psram_free": 0}})
    errors, _ = evaluate(zero_metric)
    require(any("psram_free is zero at cycle 25" in error for error in errors), errors)

    ordered_lines = valid.splitlines()
    ordered_lines[1], ordered_lines[2] = ordered_lines[2], ordered_lines[1]
    out_of_order = b"\n".join(ordered_lines) + b"\n"
    errors, _ = evaluate(out_of_order)
    require(any("cycle sequence mismatch" in error for error in errors), errors)

    bad_boundary = valid.replace(
        b"M2_STRESS COMPLETE cycles=50\nESPocket started",
        b"ESPocket started\nM2_STRESS COMPLETE cycles=50",
    )
    errors, _ = evaluate(bad_boundary)
    require(any("markers are out of order" in error for error in errors), errors)

    duplicate_begin = BEGIN_MARKER + b" app_id=2\n" + valid
    errors, _ = evaluate(duplicate_begin)
    require(any("exactly one begin marker" in error for error in errors), errors)

    malformed_records = (
        ("begin", b"M2_STRESS BEGIN cycles=49 app_id=2"),
        (
            "cycle",
            b"M2_STRESS CYCLE cycle=0 start=Running stop=Stopped gui=Unloaded "
            b"internal_free=1 psram_free=1 internal_largest=1 psram_largest=1 trailing",
        ),
        ("completion", b"M2_STRESS COMPLETE cycles=49"),
        ("startup", b"ESPocket startedness"),
    )
    for name, record in malformed_records:
        errors, _ = evaluate(record + b"\n" + valid)
        require(any(f"malformed {name} record" in error for error in errors), errors)
        require(
            capture_should_stop(begin_only + record + b"\n"),
            f"malformed in-run {name} did not stop live capture",
        )

    orphan_cycle = valid.splitlines()[1] + b"\n"
    for concatenated in (orphan_cycle + valid, valid + orphan_cycle):
        errors, _ = evaluate(concatenated)
        require(any("cycle markers exist outside" in error for error in errors), errors)

    cleanup_failure = valid.replace(
        COMPLETE_MARKER,
        b"Failed to cleanup app GUI while stopping app: scheduler unavailable\n" + COMPLETE_MARKER,
    )
    errors, _ = evaluate(cleanup_failure)
    require(any("failure signature" in error for error in errors), errors)

    for benign_watchdog_line in (
        b"wifi: watchdog disabled",
        b"D (123) task_wdt: Task watchdog timer retention initialization",
    ):
        benign_watchdog = valid.replace(
            COMPLETE_MARKER,
            benign_watchdog_line + b"\n" + COMPLETE_MARKER,
        )
        errors, _ = evaluate(benign_watchdog)
        require(not errors, errors)

    for reset_reason in (
        b"TG0WDT_CPU_RESET",
        b"TG1WDT_CPU_RESET",
        b"RTCWDT_RTC_RESET",
    ):
        reset_log = valid.replace(
            valid.splitlines()[26],
            valid.splitlines()[26] + b"\nrst:0x7 (" + reset_reason + b"),boot:0x8",
        )
        errors, _ = evaluate(reset_log)
        require(any("failure signature" in error for error in errors), errors)
        require(capture_should_stop(reset_log), f"{reset_reason!r} did not stop live capture")

    print("PASS: M2 lifecycle parser self-test")


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--port", default="/dev/cu.usbmodem2101")
    source.add_argument("--input", type=Path)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return 0

    if args.input is not None:
        data = args.input.read_bytes()
    else:
        data = capture_serial(args.port, args.timeout)
    if args.output is not None:
        args.output.write_bytes(data)

    errors, medians = evaluate(data)
    for metric, (early, late, loss) in medians.items():
        print(f"{metric}: early_median={early} late_median={late} loss={loss}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: 50/50 lifecycle cycles and heap stability criteria")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
