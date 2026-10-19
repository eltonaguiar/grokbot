# Edge proof: multi-sleeve book vs a coin flip (data to Oct 2026)

Run with `python3 -m venv .venv && . .venv/bin/activate && pip install yfinance pandas numpy scipy matplotlib && python run.py` (gates are in `edge_validator.py`; out-of-sample checks are in `oos.py`). Results are in `results.csv` and the chart is `equity_curves.png`.

Data: Yahoo adjusted closes, resampled to monthly. ETFs are extended back in time by joining them to older mutual funds that track similar assets: SPY←VFINX, TLT←VUSTX, IEF/LQD←VBMFX, SHY←FGOVX, HYG←VWEHX, GLD←FSAGX (gold-miner fund, a rough stand-in), VNQ←VGSIX, DBC←PCRIX. The quality/value sleeve uses Ken French portfolios: 50% value-weighted top-30% operating profitability plus 50% top-30% book-to-market, minus 20 bp/yr for costs. Volatility risk premium (VRP) uses the CBOE PUT index (^BXM had no history). Crypto carry was skipped.

## Key numbers (monthly, net of modeled costs)
| Strategy | Dates | CAGR | Vol | Sharpe | MDD | Win rate [Wilson 95%] | binom p | PF [boot 95%] | P(PF≤1) | DSR | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPY buy & hold | 1986–2026 | 11.2% | 15.2% | 0.78 | -50.8% | 65% [61,69] | <1e-6 | 1.78 [1.41,2.28] | 0 | – | FAIL (MDD) |
| TSMOM 1/3/12, 10% vol target (pre-registered) | 1987–2026 | 7.5% | 8.9% | 0.86 | -25.3% | 61% [57,65] | 1e-6 | 1.89 [1.50,2.43] | 0 | 0.999 (18 variants) | FAIL (MDD) |
| TSMOM, out of sample 2016+ (variant picked on pre-2015 data) | 2016–2026 | 2.4% | 8.6% | 0.31 | -18.7% | 55% [46,63] | 0.17 | 1.28 [0.80,2.08] | 0.15 | 0.48 | FAIL (PF) |
| TSMOM pre-registered, 2016+ | 2016–2026 | 1.4% | 9.1% | 0.20 | -25.3% | 54% [45,62] | 0.22 | 1.16 [0.74,–] | 0.26 | – | FAIL |
| Quality/Value (French) | 1986–2026 | 13.0% | 15.8% | 0.86 | -51.0% | 66% [62,70] | <1e-6 | 1.90 [1.50,2.44] | 0 | – | FAIL (MDD) |
| Factor-ETF blend (QUAL/VLUE/MTUM/USMV) | 2013–2026 | 13.0% | 13.9% | 0.96 | -23.9% | 67% | 8e-6 | 2.03 | 0.0004 | – | FAIL (MDD) |
| Put-write (CBOE PUT) | 1996–2026 | 8.6% | 10.5% | 0.84 | -32.7% | 74% | <1e-6 | 1.98 | 0 | – | FAIL (MDD) |
| **Combined, inverse-vol weights, 40% cap per sleeve** | 1988–2026 | 8.8% | 6.9% | **1.27** | **-20.5%** | 70% [66,74] | <1e-6 | 2.48 [1.93,3.27] | 0 | 1.0 | FAIL (MDD by 0.5 pt) |
| Combined, 2016+ | 2016–2026 | 7.3% | 7.0% | 1.04 | -11.0% | 69% [61,77] | <1e-6 | 2.10 [1.35,–] | 0.001 | – | PASS |
| **Coin-flip control** (random long/short SPY) | 1986–2026 | -5.5% | 15.6% | -0.28 | -90% | 46% | 0.98 | 0.81 [0.64,1.02] | 0.97 | – | **REJECTED** ✔ |

For comparison, SPY over the same dates had a Sharpe of 0.78 (1987+), 0.82 (1988+) and 1.00 (2016+), with an MDD of -51% (or -24% for 2016+).

Block-bootstrap MDD (12-month blocks): for the combined book, the median is -17.6%, the 5th-percentile tail is -25.7%, and P(MDD worse than -20%) = 37%. For SPY that probability is 99.7%.

Random-entry / permutation tests (share of random versions the real strategy beats):
- TSMOM vs random-sign positions with the same sizing: beats 100% of 500.
- QualVal active return vs the market: 99%.
- Put-write vs SPY: 8% (it adds no return over SPY; its benefit is lower vol only).
- Combined vs SPY on raw return: 2% (it earns less than SPY; its edge is risk-adjusted).
- Coin flip: 0%.

Correlations: TSMOM vs QualVal 0.01, TSMOM vs PutWrite -0.20, QualVal vs PutWrite 0.84. In 2008, TSMOM made +26.7% while SPY lost 36.8% and the combined book lost 11.5%.

## Verdict
- **The gates work.** They clearly reject the coin flip: p = 0.98, PF CI includes 1, and 97% of bootstraps have PF ≤ 1.
- **The edges are statistically real over the long history**, but the edge mostly comes from holding risk premia (equity beta, the put-write premium). The return-timing edge comes from TSMOM before about 2015 and from the quality/value tilt.
- **TSMOM fails out of sample from 2016 on.** Sharpe drops to 0.2–0.3 and is not significant (p ≈ 0.2), which matches the post-2012 decay in managed futures widely reported in the literature. It is still a valuable crisis hedge (2008, 2022), but on this test it does not prove it beats a coin flip after 2015.
- **The combined book is the only thing close to money-ready.** It has a higher Sharpe than SPY on every window (1.27 vs 0.82 long-run), but it narrowly fails the strict MDD ≤ 20% gate full-period (-20.5%). It passes all gates since 2016. I did **not** tune it to pass, so the honest status is NOT_READY. It is borderline, and a third of bootstrap paths breach 20%.
- No single sleeve passes, because every sleeve that holds stocks breaches the 20% MDD limit.

## Caveats
- Monthly win rate and PF mostly reward being long assets that drift up, so SPY itself "beats a coin flip" on WR. The real test of edge is Sharpe/DSR against the benchmark and the permutation tests.
- The ETF-to-mutual-fund joins are approximate (the GLD proxy holds gold miners; the DBC proxy only goes back to 2002). Survivorship: the universe is today's surviving liquid ETFs. French portfolios are gross paper returns with rebalancing costs assumed, not executed. PUT is an index, not tradable, and no costs were applied to it.
- Shorting in TSMOM ignores borrow costs and short rebates. Costs are 10 bp per side on turnover. Residual cash earns 0%, which is conservative.
- The data covers 1986–2026: one long bond bull market, then the 2022 shock. The out-of-sample period (2016+) has only 130 months.
- DSR uses 18 TSMOM variants. More analysis was done than the grid alone (3 sleeves, 1 weighting scheme), so the real trial count is somewhat higher.
- None of this is investment advice, and past results do not guarantee future returns.
