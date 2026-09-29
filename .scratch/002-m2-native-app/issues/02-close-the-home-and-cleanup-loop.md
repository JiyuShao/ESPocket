# 02 — Close the Home and cleanup loop

**What to build:** Home stops the foreground Native App in the Core task, restores Launcher and releases GUI and callback state.

**Blocked by:** 01 — Deliver a visible Native App tracer bullet.

**Status:** retrospective-resolved

- [x] Display callback publishes intent without calling Core directly.
- [x] System clears only the matching foreground generation.
- [x] GUI unload and callback cleanup are observable.

## Resolution

Accepted after the final Home concurrency remediation; earlier images remain superseded.
