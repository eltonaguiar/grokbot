# Combined-book edge proof (reference implementation)

Reference code for the combined multi-asset book: trend-following across asset classes, quality/value, and put-write, with inverse-vol weights, a 40% sleeve cap, and a 5% portfolio volatility cap.

- `run.py`: full backtest of each sleeve, the combined book, SPY, and a coin-flip control
- `edge_validator.py`: statistical gates (Wilson CI, binomial p, PF bootstrap, block-bootstrap MDD, probabilistic/deflated Sharpe, random-entry percentile)
- `oos.py`: out-of-sample (2016+) test with parameters chosen on pre-2015 data
- `volsel.py`: pre-registered volatility-cap selection (highest of 5-10% with pre-2016 MDD within -15%)
- `REPORT.md`, `results.csv`: backtest results
- `pilot/`: frozen paper pilot (`RULES.md` + SHA-256, `pilot.py`, `ledger.csv` starting at the 2026-09-30 close)

Data: Yahoo adjusted closes (yfinance) plus Ken French portfolios; raw data files are not committed. Monthly run: `cd pilot && python pilot.py`.

Not investment advice. Past results don't guarantee future returns.
