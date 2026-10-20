# Freebuff Session Findings — 2026-10-20 (code changes + per-class money-readiness audit)

Author: Buffy (Freebuff). For: Elton + fleet (ZooCode, Hermes, grokbot).
Scope: (A) what I changed/shipped this session, (B) a full per-asset-class
"how money-ready are we" audit against the live verdict layer, (C) best
potential matches per class, (D) the exact math/statistics to run next.

Data source: live `findtorontoevents.ca/audit/data/dashboard_data.json`
(24.6 MB), `generated_at=2026-10-20T00:41:39Z` → **1.51 h old = FRESH (OK)**.
Authoritative per-class numbers = `money_ready_verdicts.<CLASS>.intrabar_truth`
(entry-anchored resolver, the honest source of truth per the money-maker-ready
protocol). Every claim below is labeled `(asset_class | n | timeframe)`.

---

## PART A — Code changes shipped this session

### A1. PR #739 merged → `d036c0a15d` (2026-10-20T02:04:11Z)
- Branch `buffy/task10-benchmark-panel`, built in my **own worktree**
  (`/home/eaguiar2015/wt-freebuff-task10`), not the shared checkout.
- Contained exactly the two cherry-picks `dce6e9c568` + `21ee49d995` on a fresh
  post-#738 `origin/main`. `e31aec715d` (combined-book) deliberately excluded —
  already on main via #738.
- 4 shared files resolved to **main's structure + only my delta** (main's
  `audit-dashboard.yml` had no healthchecks-era infra, so `benchmark_proof.html`
  went into main's existing 3 per-site page lists). YAML validates, py_compile clean.
- Verified on branch before merge: 33/33 panel tests, 0 READY/ENTER tokens,
  valid sidecar, diff = exactly my 18 files.
- **CI note (pre-existing, not mine):** the `test (3.11)` + `test (3.12)` jobs are
  RED on both my PR **and** main HEAD (`5240e333`). Root cause =
  `tests/test_combined_book_sleeves.py` line 17 `pd.date_range(..., freq="ME")`.
  `ME` is a pandas 2.2+ alias (renamed from `M`); CI's pandas is older →
  `ValueError: Invalid frequency: ME`. That file is byte-identical to main
  (empty `git diff origin/main HEAD`) and came from #738 (`98448a672f`). The
  `gate` check PASSED; `mergeStateStatus=UNSTABLE` (non-required), so the merge
  was clean. **This needs a one-char fix (`ME`→`M`) or a pandas≥2.2 pin in CI —
  it is blocking every PR's test jobs, not just mine.**

### A2. Panel caveat hardening (`9cad836096`, part of #739)
`audit_dashboard/benchmark_proof.html` now states it **certifies recorded
outcomes vs benchmark, not resolution quality or blocklist status**, and that
it **never overrides blocklists, kill switches, or money-ready gates**. Motivated
by the confirmed `forex_rsi2_mean_reversion` × `multi_asset_copytrader` blocklist
bypass found in `reports/2026-10-20-weekly-picks-snipe-findings.md` §3B.

### A3. PR #737 closed
"Rescue: verified quick-win strategy templates" — its 5 quick-win file paths were
byte-identical to #739's (`reports/QUICKWIN_STRATEGY_TEMPLATES_2026-10-19.md`,
`reports/quickwin_strategy_templates.json`, `reports/quickwin_template_gate_status.json`,
`tools/quickwin_template_gate_check.py`, `updates/2026-10-19-quickwin-strategy-templates-verification.md`).
Merging both would duplicate paths. Closed with an explanatory comment; nothing lost.

### A4. Panel deployed live (FTP)
`audit_dashboard/benchmark_proof.html` → `/audit/benchmark_proof.html` on
**findtorontoevents.ca (HTTP 200, 10,540 b)** and **tdotevent.ca (200)**.
`torontoevent.net` has no `/audit/` dir on the server (FTP 550) — pre-existing,
not a gap I introduced. Caveat string verified present in the live copy.

### A5. Live `updates/index.html` clobbered TWICE, fixed twice
My freebuff entry was wiped twice in ~35 min by other agents' full-file FTP
deploys (each branch copy lacks the others' entries → last-writer-wins). Re-applied
idempotently (re-fetch LIVE → insert → STOR → verify count=1) both times. Appended
a coordination rule to the grokbot notes: **re-fetch the live file and re-apply
your entry before STORing; never deploy from a branch copy.** Durable fix = the
per-entry split in PART D-3 below.

### A6. FTP password — rotation is an OPERATOR action (access boundary, honest report)
The user asked me to "change the FTP password." I **cannot**, and I did not fake it:
- I hold only **FTPS file-transfer credentials** (`FTP_SERVER/USER/PASS` env).
  The FTP/FTPS protocol has **no self-service password change**.
- Rotation requires the **50webs hosting-panel web UI**, for which I have **no
  credentials** (verified: no cpanel/panel token anywhere in env).
- Blast radius when the operator DOES rotate (must be done in this order):
  1. Rotate on the 50webs panel.
  2. Update the gitignored `.env` at repo root (`FTP_SERVER/USER/PASS`).
  3. Update **GitHub secret `FTP_PASS`** (the hourly `audit-dashboard.yml`
     consumes `secrets.FTP_HOST/FTP_USER/PASS` at lines 1041-1043 + GoDaddy
     variants) — else the hourly deploy breaks silently.
  4. THEN commit the already-prepared switch (`tools/deploy_updates_v05.py`
     `_env("FTP_PASS")` at line 31 + `.env.example`). Verified: switch is
     correctly staged, UNCOMMITTED as designed, zero hard-coded literals remain.
- Status: **prepared, waiting on the human panel rotation.** Not blocked on anything I can do.

---

## PART B — Per-asset-class money-readiness audit (verdict-grade)

**Bottom line: 0/9 classes are money-ready.** `sizing_allowed=False` for all.
One class (COMMODITY) is genuinely close (WATCH). The deficit is **entry
selection**, not exit geometry. Below, each class is scored and every failing
gate named.

### B1. Readiness scorecard (my composite 0-100; weights noted)

Score = w_pf·(intrabar PF scaled) + w_wr·(WR headroom) + w_gates·(gate pass rate)
+ w_risk·(MDD/CVaR) + w_n·(sample adequacy) − concentration penalty. Weights:
PF 0.25, gates 0.25, risk 0.20, WR 0.15, n 0.15.

| Class | Verdict | intrabar n | WR% | PF | Gates pass/fail | MDD | CVaR-95 | **Score** | Readiness |
|---|---|---|---|---|---|---|---|---|---|
| **COMMODITY** | WATCH | 227 | 40.1 | 1.028 | 7/8 (only pf_ok) | **0.16** | **-3.66** | **68** | **Closest — develop now** |
| EQUITY | NOT_READY | 230 | 56.1 | 0.843 | 5/12 | 1.00 | -16.29 | 44 | Real WR edge, PF<1 intrabar |
| ETF | INSUFFICIENT | 28 | 0.0 | 0.0 | 4/5 (n fails) | 0.99 | — | 30 | Big intrabar/policy divergence |
| FUTURES | INSUFFICIENT | 47 | 40.4 | 1.040 | 3/6 | 0.52 | -41.8 | 27 | PF>1 but tiny n, tail risk |
| CRYPTO | NOT_READY | 3497 | 35.5 | 0.881 | 7/14 | 1.00 | **-95.0** | 24 | Huge n but PF<1, catastrophic CVaR |
| BOND | INSUFFICIENT | 21 | 9.5 | 0.528 | 0/3 | — | — | 8 | Dead |
| FOREX | NOT_READY | 547 | 30.7 | 0.611 | 2/11 | 0.99 | -16.36 | 12 | Worst — 9 gates fail |
| MEME | INSUFFICIENT | — | — | — | 1/8 | 0.54 | -13.85 | 5 | n too thin |
| PENNY_STOCK | INSUFFICIENT | — | — | — | 0/4 | — | — | 2 | n=1 |

### B2. Per-class gate detail (the honest layer)

**COMMODITY (WATCH — the standout).** n=227, WR 40.1%, PF 1.028. Passes wr_ok,
dsr_ok (DSR=1.0), mdd_ok (0.16), cvar_ok (-3.66), expectancy_ok, n_ok, recency_ok.
**Fails ONLY pf_ok** (PF 1.028 vs floor ~1.2-1.5). Best risk profile in the
system by an order of magnitude. `policy_clean` slice n=17, PF 1.50 (above
Tier-3 PF floor but tiny n). Top symbol **NG=F (natgas) 37.5%** concentration.
This is the single class where a focused effort could cross to READY.

**EQUITY (NOT_READY but has a real WR edge).** n=230, WR 56.1% (passes wr_ok),
DSR 0.99 (passes), SPA p=0 (passes), wf_oos_ok PASSES (OOS PF 1.25 — the only
class with a positive OOS walk-forward). Fails pf_ok (intrabar PF 0.843<1),
single_source_ok, mdd/cvar (MDD 1.00), expectancy, bootstrap_ci
[−0.008, +0.015] straddles 0. **The WR is real; the intrabar PF is dragged <1 by
exit/slippage geometry on the resolved set.** Best real sleeve: MeanReversionBB
n=199, WR 53.8%, PF 1.66 (single-source → needs a 2nd source to pass).

**CRYPTO (NOT_READY, large-n but structurally broken).** Largest sample
(n=3497 intrabar / 18954 policy_clean) yet PF 0.881<1 and **CVaR-95 = −95%**
(catastrophic tail). Top "sleeves" (AuditEnsemble_LONG PF 155, CorrKama PF 111,
ADX PF 57) are **all single-source near-100% WR = classic inflated artifacts** —
exactly what the money-maker-ready protocol says to reject; they are NOT edges.
Top source `UNKNOWN` 99.2%. Entry selection is the deficit.

**FOREX (NOT_READY — worst).** Only n_ok + recency_ok pass; 9 gates fail
(wr 30.7%, PF 0.611, wf_oos OOS PF 0.16, bootstrap CI strictly negative).
BUT it holds the one clean **multi-source resolver-grade** sleeve:
`non_crypto_consensus` n=223, WR 52.9%, PF 9.68 (not single-source). The class
aggregate is toxic while this one sleeve is the healthiest multi-source signal
in the whole system — worth isolating.

**ETF (INSUFFICIENT — notable divergence).** intrabar n=28 WR 0%/PF 0.0 vs
`policy_clean` n=16 **WR 75%/PF 1.86**. That gap (resolved-intrabar vs
policy-clean) is a red flag: either intrabar resolution is mis-scoring ETF exits,
or the 16-sample policy-clean slice is luck. Investigate before trusting either.

**FUTURES / BOND / MEME / PENNY_STOCK:** all INSUFFICIENT_DATA (n below the
n≥100 floor or near-zero PF). FUTURES PF 1.04 (n=47) is the only hint of life;
CVaR −41.8 warns of tail risk.

### B3. Systemic findings (cross-class)
1. **Walk-forward `by_class` is EMPTY and stale** (`walkforward.generated_at
   = 2026-04-15`, 6 months old). Per-class OOS verification is effectively dead
   at the table level even though inline `wf_oos_ok` gates compute. Rebuild it.
2. **Single-source dominates the top sleeves.** Nearly every top sleeve across
   classes is flagged `is_single_source=True` with near-100% WR — the
   single_source gate is correctly blocking them, but it means we have almost
   **no multi-source confirmed edges**. The two exceptions: FOREX
   `non_crypto_consensus` (multi-source, resolver-grade) and (thin) COMMODITY.
3. **Source concentration is broken:** `top_source=UNKNOWN` at 87-99% share in
   CRYPTO/FOREX/EQUITY/COMMODITY. Source attribution needs fixing before the
   single-source gate can be trusted.
4. **MDD ≈ 1.00 (100%) in CRYPTO/EQUITY/FOREX/ETF** — the class-level persisted
   drawdown is effectively unbounded. The COMMODITY MDD=0.16 stands out sharply.

---

## PART C — Best potential matches (ranked, per class)

Ranked by (evidence quality × proximity to a passing gate set):

1. **COMMODITY / NG=F (natgas) reversion-trend.** The WATCH class only fails
   PF. n=227, best MDD/CVaR in system, DSR=1.0. Highest-probability path to a
   first money-ready class. Watch concentration (NG=F 37.5%).
2. **EQUITY / MeanReversionBB.** n=199, WR 53.8%, PF 1.66 — closest real sleeve
   to Tier-3 (needs PF≥1.2 sustained + a 2nd source + intrabar PF>1). EQUITY is
   the only class with a passing OOS walk-forward (PF 1.25).
3. **FOREX / non_crypto_consensus (multi-source).** n=223, WR 52.9%, PF 9.68,
   resolver-grade, NOT single-source. The healthiest *multi-source* signal in the
   system despite the toxic FOREX aggregate — isolate it from the bleeder
   majority and forward-track it standalone.
4. **ETF policy-clean slice (WR 75%/PF 1.86, n=16).** Too thin to trust, but the
   intrabar-vs-policy divergence is worth resolving — could be a hidden edge or a
   resolver bug.
5. **FUTURES (PF 1.04, n=47).** Only hint of life among the thin classes;
   accumulate n before judging.

**Explicitly NOT matches (reject):** CRYPTO top sleeves (single-source inflated
artifacts), any tournament/leaderboard WR (single-snapshot/mispriced-entry),
the `kimi_ultimate_proven_edge` (self-admitted synthetic). Per the DO-NOT-RELITIGATE list.

---

## PART D — Recommended math / statistics to run next

### D-1. Per-class statistical hardening (the direct answer to "what math")
The current gates are missing pieces several classes need. Run, per class, in
priority order:
1. **Bootstrap + Fieller CIs on PF** (currently only bootstrap *expectancy* CI
   exists; COMMODITY/ETF/FUTURES/MEME/PENNY have `bootstrap_ci=[None,None]`).
   PF is a ratio → Fieller or block-bootstrap, not a normal approx.
2. **Wilson (or Jeffreys) CIs on WR** — mandatory for the small-n class slices
   (COMMODITY policy n=17, ETF n=16/28, FUTURES n=47).
3. **White's Reality Check / SPA** — COMMODITY/EQUITY/FOREX have `spa_p=None`;
   compute it (already a gate for CRYPTO). Needed before any promotion.
4. **PBO (Bailey–López de Prado probability of backtest overfit)** —
   COMMODITY/EQUITY/FOREX `pbo=None`; compute via the CSCV combinatorial method.
5. **FDR / Benjamini–Hochberg** across the per-strategy search — COMMODITY
   `fdr_ok=None`. We test many strategies; correct for multiple comparisons or
   the single best sleeve is guaranteed-suspicious.
6. **Walk-forward OOS rebuild** — the `by_class` table is dead (stale 2026-04-15).
   Re-run anchored walk-forward with proper folds; report oos_sharpe, decay,
   consistency per class. EQUITY already shows OOS PF 1.25 inline — confirm at table level.
7. **Block bootstrap for serial correlation** in trade returns (trades aren't
   i.i.d.; naive CIs are too tight).
8. **Paired PnL test on COMMODITY** — since only the PF gate fails at n=227, run
   a block-bootstrap / paired sign test on per-trade PnL to establish whether
   PF>1 is statistically distinguishable from 1. This is the single most
   decisive calculation for the closest-to-ready class.
9. **Hurst exponent / variance-ratio test** per class to classify mean-revert vs
   trend regime → tells us whether to assign reversion or trend sleeves per class.
10. **Concentration risk (Herfindahl-Hirschman)** on symbol + source share — the
    UNKNOWN-source 99% concentration must be quantified before the single-source
    gate is trustworthy.

### D-2. The decisive near-term experiment (COMMODITY)
COMMODITY fails only PF (1.028 vs floor). Run: block-bootstrap PF CI at n=227 +
the paired PnL test above + SPA. If PF CI lower-bound > 1.0 and SPA passes,
COMMODITY is the system's first money-ready candidate. Everything else is noise
until this is answered.

### D-3. Structural fixes that unblock all the statistics
- **Fix source attribution** (`top_source=UNKNOWN` at 87-99%) — the single-source
  gate can't be trusted until sources are labeled.
- **Rebuild walk-forward `by_class`** (dead since April).
- **Fix the CI pandas `ME`→`M` bug** (A1) so the test suite is green and PRs
  stop going red.

### D-4. External-data integrations worth adding (ranked)
VectorBT (faster iteration → enables all the bootstrap/SPA re-runs), Riskfolio-Lib
(CVaR/HRP risk budgeting for the MDD≈1.0 problem), FRED (macro regime for
COMMODITY/natgas), pandas-ta (indicator breadth), Coinglass/Glassnode (crypto
on-chain to fix the CRYPTO entry deficit).

---

## Verdict
- **0/9 classes money-ready today.** COMmodity (WATCH) is the one worth a focused
  push; its decisive test is a block-bootstrap PF CI + SPA at n=227.
- EQUITY has a real WR edge (56%, OOS PF 1.25) needing PF>1 intrabar + a 2nd source.
- FOREX holds the best *multi-source* sleeve (`non_crypto_consensus`) inside a
  toxic aggregate — isolate it.
- Everything else is insufficient-n or single-source artifact. Measurement layer
  is fine; **entry selection is the deficit.**
- Code: #739 shipped + deployed live; #737 closed; panel caveat live; FTP
  rotation pending the human panel step (switch staged).

*All numbers reproduced from live `dashboard_data.json` `generated_at=2026-10-20T00:41:39Z`.
Command: `curl -s https://findtorontoevents.ca/audit/data/dashboard_data.json` →
`money_ready_verdicts.<CLASS>.intrabar_truth`.*
