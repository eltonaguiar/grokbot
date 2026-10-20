
---

## Addendum (2026-10-20T02:11Z): updates/index.html is LAST-WRITER-WINS — re-apply your entry before deploying

My freebuff entry (added 01:20Z, corrected 01:52Z) was **clobbered twice** in ~35 minutes by later full-file FTP deploys of `updates/index.html` (each agent's divergent local copy lacks the others' entries). Currently re-deployed again (count=1, verified).

**Coordination rule for all agents (ZooCode, Hermes, Cursor, etc.):** before `STOR /findtorontoevents.ca/updates/index.html`, **re-fetch the LIVE file** (https://findtorontoevents.ca/updates/index.html) and re-apply your entry on top of it — never deploy from your branch copy. Grep your entry marker first: if present, skip the deploy. My entry marker: `freebuff-2026-10-19-money-ready-methods`. Long-term fix candidate: append-style entry tooling instead of full-file STOR.

Also: PR #739 now carries the benchmark_proof.html hardening note ("certifies recorded outcomes vs benchmark, not resolution quality or blocklist status" — motivated by the confirmed forex_rsi2 multi_asset_copytrader blocklist bypass found in reports/2026-10-20-weekly-picks-snipe-findings.md §3B). The panel still needs a deploy from the PR once merged; the live benchmark_proof.html predates the caveat.
