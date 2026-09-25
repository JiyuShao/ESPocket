#!/usr/bin/env python3
"""Reset ESPocket and check whether System Core initialization completes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time

import serial


ANSI_ESCAPE = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")
SYSCORE_MARKER = b"SysCore: [lifecycle.cpp:0070] (init) : Version: 0.8.4"
SUCCESS_MARKER = b"ESPocket started"


def reset_board(port: str) -> None:
    command = [
        sys.executable,
        "-m",
        "esptool",
        "--chip",
        "esp32s3",
        "--port",
        port,
        "--before",
        "default-reset",
        "--after",
        "hard-reset",
        "read-mac",
    ]
    last_error = ""
    for _ in range(3):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return
        last_error = result.stderr.strip() or result.stdout.strip()
        time.sleep(0.5)
    raise RuntimeError(f"Failed to reset board: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/cu.usbmodem2101")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    reset_board(args.port)
    deadline = time.monotonic() + args.timeout
    captured = bytearray()

    with serial.Serial(args.port, 115200, timeout=0.1) as monitor:
        while time.monotonic() < deadline:
            chunk = monitor.read(monitor.in_waiting or 1)
            if chunk:
                captured.extend(chunk)
                if SUCCESS_MARKER in captured:
                    print("PASS: ESPocket completed startup")
                    return 0

    clean = ANSI_ESCAPE.sub(b"", bytes(captured)).replace(b"\r", b"")
    lines = clean.decode("utf-8", errors="replace").splitlines()
    for line in lines[-20:]:
        print(line)

    if SYSCORE_MARKER in clean:
        print("FAIL: entered System Core init but did not complete", file=sys.stderr)
        return 1

    print("INCONCLUSIVE: System Core init marker was not observed", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
