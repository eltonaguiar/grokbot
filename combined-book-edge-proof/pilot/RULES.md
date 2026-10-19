# Paper pilot: combined book, frozen rules v1 (frozen 2026-10-19)

**Start:** positions set at the 2026-09-30 close. The first paper return is recorded at the Oct 2026 month-end. Paper only, no live capital.

## Data
- Yahoo Finance adjusted closes (total return). Signals use month-end closes, meaning the last trading day of the month.
- A month is processed only after it has fully closed.

## Sleeves (tradeable ETFs only)
1. **TSMOM**
   - Universe: SPY EFA EEM IWM TLT IEF SHY LQD HYG TIP GLD DBC USO SLV VNQ.
   - Signal per asset: the average of sign(1-month), sign(3-month) and sign(12-month) total return, a value in [-1, 1].
   - Raw weight = signal × 0.10 / (63-day daily vol × √252) / √(number of assets with signals).
   - Each asset is clipped to ±1. If gross exposure is above 2.0, all weights are scaled down to 2.0.
2. **Quality/Value:** 50% QUAL + 50% VLUE.
3. **Put-write:** 100% XYLD (S&P 500 BXM covered call). PUTW was delisted; covered call ≈ cash-secured put by put-call parity.

## Book construction
- Sleeve weight ∝ 1 / (36-month std of the sleeve's monthly returns), computed on backtested sleeve returns from the same ETFs. At least 24 months are required.
- Each sleeve is capped at 40%, with no redistribution. Whatever is left is cash earning 0%.
- **Vol-target overlay:** scale = min(1.0, 0.05 / (book's trailing 12-month realized vol, annualized)). No leverage.
- **Choosing the target:** the rule, set in advance, was "the highest target in {5,6,7,8,9,10}% whose pre-2016 backtest MDD stays inside the 15% kill limit." It was evaluated on pre-2016 data only and gave **5%**: pre-2016 MDD -14.4%, versus -16.5% at 6%.
- Final asset weights = overlay × Σ(sleeve weight × weight inside the sleeve). Rebalanced monthly.
- Cost: 10 bp × turnover (sum of absolute weight changes) is charged each month.

## Gates (live paper months only)
- Reported: Wilson 95% CI on win rate; one-sided binomial p (H1: WR > 50%); PF with bootstrap CI and P(PF ≤ 1); MDD; Sharpe of the book vs SPY over the same months.
- **READY:** n ≥ 100, PF ≥ 1.5, WR ≥ 50% and MDD ≥ -20%. Otherwise **NOT_READY**.
- **KILL** (overrides everything):
  - live paper drawdown worse than -15% at any time, or
  - at n ≥ 24 months, any of: PF < 1.0, WR < 50%, Sharpe ≤ 0, or P(PF ≤ 1) > 0.5.

## Change control
- The SHA-256 of this file is stored in RULES.sha256 and hard-coded in pilot.py. Any edit aborts the run.
- Any change means a new version (v2) with a new ledger. The live record does not carry over.
