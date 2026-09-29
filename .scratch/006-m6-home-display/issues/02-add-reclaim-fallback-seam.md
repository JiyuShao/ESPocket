# 02 — Add a controllable reclaim fallback seam

**What to build:** A default-off test path that invalidates the current resume target so hardware acceptance can prove fallback to Watch Face.

**Blocked by:** 01 — Implement Watch Face Home and Display State.

**Status:** ready-for-agent

- [ ] The test seam cannot activate in normal product use.
- [ ] It invalidates the target without introducing a general memory manager.
- [ ] The next wake reaches Watch Face without restarting the App.
