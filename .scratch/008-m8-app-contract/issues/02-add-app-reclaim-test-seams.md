# 02 — Add Native and Runtime reclaim test seams

**What to build:** Default-off paths that reclaim each App model and invalidate old pages without implementing a general low-memory killer.

**Blocked by:** 01 — Complete the shared contract source.

**Status:** ready-for-agent

- [ ] Native and Runtime can be reclaimed independently.
- [ ] Old pages and transient Overlay state become invalid.
- [ ] Relaunch starts at App Root.
