# Blocklist Enforcement Fix + Per-Asset-Class Money-Ready Analysis

**Date:** 2026-10-20
**Author:** Zoo
**Repo:** findtorontoevents_antigravity.ca (work performed) → documented in grokbot

---

## Part 1 — Copy-Trader Blocklist Enforcement Bug

### What was broken

`alpha_engine/forward_validator.py::save_active_picks()` is the **canonical recording path** to
`active_picks.json` (used by 11+ emitters). It already filtered by:

1. core-whitelist kill list (`core_whitelist.json`, 539 entries)
2. `BLOCKED_SYMBOLS` (from `audit_trail/quality_gates.py`)

…but it did **NOT** filter by the canonical `config.BLACKLISTED_STRATEGIES`. So any emitter that
bypassed `production_scanner`'s emitter discipline could persist a **blacklisted** strategy pick to
`active_picks.json`. This was a real, open bypass.

### Evidence

A live scan of `alpha_engine/data/active_picks.json` before the fix found **29 blacklisted-strategy
rows**, e.g.:

- `multi_asset_forex_rsi2_mean_reversion::EURUSD=X`
- `pm_consensus_SOLUSDT_202606210555`

### The fix

Added a **BLACKLISTED_STRATEGIES defense-in-depth filter** inside `save_active_picks()`, immediately
after the `BLOCKED_SYMBOLS` filter. It is **fail-open** (a missing import never crashes the save):

```python
# -- BLACKLISTED_STRATEGIES defense-in-depth filter --
try:
    from alpha_engine.config import BLACKLISTED_STRATEGIES as _BLACKLIST
    _bl_lc = {str(s).lower() for s in _BLACKLIST}
    _before = len(picks)
    picks = [
        p for p in picks
        if str(p.get("strategy") or p.get("strategy_name") or "").lower().strip() not in _bl_lc
    ]
    _removed = _before - len(picks)
    if _removed:
        print(f"  [BLACKLISTED_STRATEGIES] Filtered {_removed} blacklisted picks before save")
except Exception:
    pass  # fail-open: never let a missing import crash the save
```

### Audit completeness (other paths already enforced)

| Path | Enforcement status |
|------|--------------------|
| `copy_trader_bridge.py::_qualify_copy_pick` | ✅ has `_BLACKLISTED_LC` check (~L209) |
| `smart_picks_engine.py::score_pick` | ✅ filters `BLACKLISTED_STRATEGIES` (PR #740) |
| `outcome_resolver.py::resolve_single_pick` | ✅ short-circuits blacklisted (PR #740) |
| `production_scanner.py` | ✅ `apply_emitter_discipline` at intake + FINAL KILL LIST |
| `backfill_local_sources.py::insert_pick/insert_outcome` | ✅ `is_emission_allowed` gate |
| `mysql_trading_sync.py` | ✅ `is_emission_allowed` gate for new rows |
| `emitter_discipline.py::is_emission_allowed` | ✅ central kill gate |
| **`forward_validator.py::save_active_picks`** | ✅ **FIXED — now filters `BLACKLISTED_STRATEGIES`** |

### Verification

- **RED** (before fix): `tests/test_forward_validator_save_blacklist.py` → 9 failed / 18 passed;
  live-leak test reported 29 leaks.
- **GREEN** (after fix): **27 passed / 0 failed**.
- **Regression**: `test_blacklist_enforcement.py`, `test_emitter_discipline_p0b.py`,
  `test_blacklist_exec_gate_enforcement.py`, `test_code_review_apr22_bugfixes.py`,
  `test_forward_validator_save_blacklist.py` → **120 passed / 0 failed**.
- Live active_picks.json assert after fix: **0 blacklisted leaks** (was 29).

---

## Part 2 — Per-Asset-Class Money-Ready Analysis

Source data: `audit_dashboard/data/money_ready_verdict.json` (generated 2026-10-19),
`pf_registry.json` (policy-clean net), `top_notch_money_ready.json`.

### Verdict summary (9 classes)

| Asset class | Verdict | n_clean | WR% | PF | DSR | Policy-clean net (n / PF) |
|-------------|---------|---------|-----|----|-----|---------------------------|
| BOND | INSUFFICIENT_DATA | 0 | 0.0 | 0.0 | — | n=0 |
| COMMODITY | WATCH | 227 | 40.1 | 1.03 | 1.0 | n=9 / PF=0.89 |
| CRYPTO | NOT_READY | 3497 | 35.5 | 0.88 | 0.0 | n=218 / PF=0.99 |
| EQUITY | NOT_READY | 230 | 56.1 | 0.84 | 0.99 | n=46 / PF=1.23 |
| ETF | INSUFFICIENT_DATA | 15 | 73.3 | 1.83 | — | n=1 / PF=0.0 |
| FOREX | NOT_READY | 547 | 30.7 | 0.61 | 0.0 | n=28 / PF=0.04 |
| FUTURES | INSUFFICIENT_DATA | 47 | 40.4 | 1.04 | 0.006 | n=13 / PF=0.76 |
| MEME | INSUFFICIENT_DATA | 13 | 7.7 | 0.02 | NaN | — |
| PENNY_STOCK | INSUFFICIENT_DATA | 1 | 0.0 | 0.0 | — | n=1 / PF=0.0 |

**Headline:** 0/9 classes are money-ready under Tier-2 policy (n≥100 policy-clean, PF≥1.5,
WR≥50%, MDD<20%). The class closest to Tier-2 by **policy-clean net is `EQUITY`** (PF=1.23,
WR=56.5%, n=46) — it needs more clean n and PF≥1.5.

### Best potential matches per asset class (from top_notch_money_ready.json)

| Class | Best matches | Metric evidence |
|-------|--------------|-----------------|
| **CRYPTO** | `FETUSDT` (luxalgo_confluence/beta_mom, WR 81.2%, n=69), `TONUSDT` (prediction_market_consensus, WR 71.2%, n=59), `STRKUSDT` (inverse_ml_enhanced, WR 69.8%, n=63) | High WR in resolved; MC mean +2.89, prob_pos 1.0 |
| **EQUITY** | `GOOGL` (smart_money_accum/momentum_rider, WR 100%, n=17), `INTC` (regime/rsi2, WR 54.5%, n=11) | WR 100% n=17 is promising but n too small; needs n→100 |
| **FOREX** | `GBPUSD=X` (cta_cross_asset_tsmom/combined_conf, WR 58.8%, n=114), `EURGBP=X` (cta/meanrev, WR 56.1%, n=171), `USDCHF=X` (carry_mom, WR 60.6%, n=99) | Only proven `cta_cross_asset_tsmom`; overall class verdict FAIL |
| **FUTURES** | recent strong YM/NQ (STABLE_EDGE some PF~2 WR~50) | low implied vol vs crypto |
| **BOND** | TLT/IEF (defensive, RVOL~5–9%) | paper-pilot only, safest vol profile |

### Recommended math / statistics to run

To move classes from INSUFFICIENT/NOT_READY → WATCH/MONEY_READY, the following should be run:

1. **Forward n-accumulation** (already the bar): each candidate sleeve must accumulate
   `n_clean ≥ 100` resolved under policy-clean gates, then re-evaluate.
2. **Deflated Sharpe Ratio (DSR)** and **Probabilistic Sharpe Ratio (PSR)** on each top match to
   confirm the edge survives multiple testing (Lopez de Prado). DSR already present in
   `money_ready_verdict`; use it per-sleeve, not just per-class.
3. **Multiple-testing correction** — apply **FDR (Benjamini–Hochberg)** across the per-symbol /
   per-sleeve candidates to avoid cherry-picking high-WR small-n symbols (n=17 GOOGL etc.).
4. **PBO (Probability of Backtest Overfitting)** / **CPCV (Combinatorially Symmetric Cross-
   Validation)** on walk-forward OOS to certify that measured edge is not overfit.
5. **Sequential Probability Ratio Test (SPRT)** on live forward picks to decide early whether a
   sleeve is truly positive (stop early if it diverges from expectation).
6. **Bootstrap / Monte Carlo** on each class's PF and WR (1000+ resamples) to compute
   CIs and the probability that PF≥1.5 is robust.
7. **Expected shortfall / CVaR + max drawdown** — MDD<20% gate is already a hard requirement;
   confirm new sleeves don't violate on forward data.

### What I recommend building next

- A **per-sleeve forward tracker** keyed by (asset_class, strategy) that accumulates n_clean and
  re-runs DSR/FDR/SPRT as n grows, so classes can be promoted exactly when they cross thresholds.

---

*NFA — research/paper trading only. 0/9 classes are money-ready.*
