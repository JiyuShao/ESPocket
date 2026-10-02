#!/usr/bin/env python3
"""Compatibility entry point; use run_device_tests.py for new invocations."""
from run_device_tests import main

if __name__ == '__main__':
    raise SystemExit(main())
