# OpenCode Findings — findtorontoevents.ca/audit Top-Notch Trades & Money-Ready Analysis

**Author:** OpenCode (opencode/beam-free)
**Generated:** 2026-10-20T02:16:30Z
**Repo of analysis:** findtorontoevents_antigravity.ca
**Target repo for this doc:** eltonaguiar/grokbot

## 1. Problem investigated
findtorontoevents.ca/audit was supposed to surface **copy-trader** picks and an **extraction of top-notch trades**. In practice the Smart Picks tab showed 0 picks — no top-notch trades from copy trader or any other source.

## 2. Root cause
`audit_trail/dashboard_generator.py` built `picks.smart_picks` solely from active picks passing `audit_trail/quality_gates.passes_smart_gate`. Of the 23 active picks in the live payload (generated 2026-10-19T19:40Z), every one failed:
- `forward_validated=false` — 6 picks (super_signals x4, QQQ, PA=F)
- per-class visibility floor (`_gate_passed=false`, `_below_gate=true`) — 8 picks (ADBE, EURGBP=X, NVDA, USDJPY=X, GC=F, YM=F, TQQQ, EFA)
- score / RR / consensus floors — the remainder

Meanwhile the curated `smart_picks_feed` already contained 1 vetted pick (ETHUSDT SHORT, `copy_hl_RTB_2`, source `copy_trader_intel`) that was never promoted into `picks.smart_picks`. So the extraction existed but its output was dropped at the dashboard layer.

## 3. Fix applied (revised after review)
`smart_picks` stays strictly gate-validated (quality gates only). Unvalidated curated picks are NOT promoted as Smart Picks. Instead:
- `picks.curated_feed`: curated smart_picks_feed picks labeled "Curated – not gate-validated" (separate field).
- `picks.smart_picks_gate_failures`: counts per failed gate.
- `picks.smart_picks_near_miss`: top 3 near-miss picks with their failed gate (contingency for empty state).

PR: opencode/audit-empty-state (not merged). Supporting doc: `updates/2026-10-20-audit-empty-state.md`.

## 4. Money-ready status per asset class (from live payload)
Tier thresholds (PERFORMANCE_CHARTER): T1 PF≥2.0/WR≥55%/MDD≤10%/n≥200; T2 PF≥1.5/WR≥50%/MDD≤20%/n≥100; T3 PF≥1.2/WR≥45%/MDD≤25%/n≥100.

| Class | n (resolved) | WR% | PF | MDD% | Intrabar n/WR/PF | Status | Money-ready? |
|---|---|---|---|---|---|---|---|
| CRYPTO | 19621 | 45.7 | 0.29 | 100 | 3497 / 35.5 / 0.88 | stressed | NO |
| EQUITY | 463 | 55.3 | 0.88 | 100 | 230 / 56.1 / 0.84 | watch | NO (PF<1) |
| FOREX | 374 | 32.9 | 0.31 | 98.6 | 547 / 30.7 / 0.61 | stressed | NO |
| ETF | 15 | 73.3 | 1.83 | n/a | n/a | thin_sample | NO (n<100) |
| COMMODITY | 18 | 33.3 | 1.32 | 0.16 | 227 / 40.1 / 1.03 | thin_sample | NO |
| FUTURES | 12 | 8.3 | 0.45 | 17.6 | 47 / 40.4 / 1.04 | thin_sample | NO |
| BOND | 0 | 0 | n/a | n/a | n/a | insufficient_data | NO |

Verdict: 0/7 asset classes money-ready. CRYPTO/EQUITY/FOREX have sufficient n but PF<1. ETF/COMMODITY/FUTURES/BOND thin or insufficient.

## 5. Walk-forward verification
`walkforward.by_class` is EMPTY in the payload (last generated 2026-04-15, stale). No OOS evidence → every class UNVERIFIED for walk-forward. Action: regenerate walk-forward artifacts.

## 6. Cumulative system winners (n≥100, PF≥1.5, WR≥50)
| System | n | WR% | PF | MDD% | Asset classes | Notes |
|---|---|---|---|---|---|---|
| multi_asset_copytrader | 237 | 54.5 | 3.24 | 1.9 | COMMODITY,EQUITY,FOREX,FUTURES | Banned for data-integrity (CADJPY +427% feed bug) |
| mega_mutation | 729 | 60.0 | 2.49 | 64.2 | CRYPTO | MDD too high |
| battleground | 122 | 56.6 | 1.76 | 7.3 | CRYPTO | Only Tier-2 candidate; needs n≥200 |

## 7. System draggers (most negative PnL)
rapid_fire (-167, PF0.28), luxalgo_filters (-161, PF0.97, n=3786), mercury2_fast (-140), aggregated_picks (-65), ml_bg_system_b (-55), ml_bg_system_a (-50), ml_bg_ensemble (-30), copy_trader_clones (-13, PF0.52), breakout_c_spike (-12), signal_aggregator (-6), paper_trading (-5), goldmine_stocks (-5, PF0.42).

## 8. Best potential matches (edges to pursue)
- battleground (CRYPTO): PF 1.76, WR 56.6, MDD 7.3, n=122 — closest to Tier-2; needs n≥200 and PF≥2.0.
- multi_asset_copytrader: PF 3.24 but banned; if re-validated on clean data, strong cross-asset sleeve.
- mega_mutation: PF 2.49 but MDD 64.2 — needs volatility scaling / position sizing.
- ETF n=15 WR 73.3 PF 1.83 — tiny sample; promising, needs n≥100.

## 9. Math / statistics to run
1. Intrabar re-resolution: `tools/reresolve_intrabar.py` (dry-run then --apply) for entry-anchored TP/SL.
2. Clean-cohort screen: exclude backfill resolvers, banned sources, sane-pnl guard, count EXPIRED as non-win; require ≥3 months n≥30/mo.
3. Walk-forward OOS: populate `walkforward.by_class` with folds, oos_wr, oos_wr_std, oos_sharpe, decay, consistency.
4. Per-class stat-sig gates (Layer 2.5): n≥8, WR≥52%, PF≥1.5 for (symbol,strategy,source) triples.
5. Concept-drift KS test: `hf_stats.concept_drift`; auto-pause if D>0.10.
6. MDD/volatility scaling for mega_mutation to push MDD≤20.
7. Backtest-overfit detector: `fwd_vs_bt_divergence.rows` grouped by system family; surgical quarantine.
8. Entry-condition stamping: `tools/stamp_entry_conditions.py` → `entry_conditions_forward.json` (RSI 50-70 x US session) until n≥100 + R1/R2/R3 re-pass.

## 10. Best-Possible-Action (ranked)
P0: Fix intrabar resolution + walk-forward regeneration (measurement first).
P1: Re-baseline clean cohort; paper-pilot ≥4wk; ban FOREX bleeders; wire emitter discipline.
P2: Academic sleeves (TSMOM, residual momentum, carry) with trailing-stop exits.
P3: ETF emitter expansion; drift auto-pause; FRED_API_KEY.
Never promote from: 14d pick summaries alone, AI tournament WR, 32.6M backtest rows.

## 11. Areas for further research
- Why `forward_validated` is false for the majority of active picks and how to set it correctly.
- Whether the per-class visibility floor (`_visibility_floor: per_class`) is too aggressive for non-crypto classes.
- Data-integrity re-validation of banned sources (multi_asset_copytrader) on clean intrabar data.
- Walk-forward regeneration pipeline (currently empty/stale).
- MDD reduction for mega_mutation (currently 64.2%).
- ETF sample expansion (n=15 → target 100+).

## 12. Verifiable claims log
- Payload: `audit_dashboard/data/dashboard_data.json` generated_at 2026-10-19T19:40:11Z.
- Fix scope: `audit_trail/dashboard_generator.py` (smart_picks fallback).
- Money-ready verdict: 0/7 classes (intrabar_truth PF: CRYPTO 0.88, EQUITY 0.84, FOREX 0.61, COMMODITY 1.03, FUTURES 1.04).
"