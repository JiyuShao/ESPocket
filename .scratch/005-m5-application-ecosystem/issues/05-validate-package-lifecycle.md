# 05 — Validate the remote package lifecycle

**What to build:** A compatible signed package completes download, verification, install, launch, update, reboot discovery and uninstall without violating Runtime isolation.

**Blocked by:** 03 — Enforce package trust; 04 — Project dynamic Launcher; official HTTP fix; Runtime keyboard owner isolation.

**Status:** needs-info

- [ ] Every lifecycle transition has physical and serial evidence.
- [ ] Native and existing Runtime Apps remain stable.
- [ ] Long-run package lifecycle has no reboot, stale entry or permission leak.
