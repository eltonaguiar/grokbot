"""Monthly paper-pilot runner for frozen rules v1. Usage: python pilot.py"""
import hashlib, json, os, sys, datetime as dt
import numpy as np, pandas as pd, yfinance as yf
from edge_validator import winrate, pf_boot, perf
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
RULES_SHA = 'd5bed907932009a96d45521c15102cba2092ec9307dfd8367aedf3f21c9fcfd5'
TS = ['SPY','EFA','EEM','IWM','TLT','IEF','SHY','LQD','HYG','TIP','GLD','DBC','USO','SLV','VNQ']
QV = {'QUAL': 0.5, 'VLUE': 0.5}; PW = {'XYLD': 1.0}
ALL = sorted(set(TS) | set(QV) | set(PW)); COST = 0.001; CAP = 0.40; VT = 0.05; START = pd.Timestamp('2026-09-30')
LEDGER = 'ledger.csv'

def check_hash():
    h = hashlib.sha256(open('RULES.md', 'rb').read()).hexdigest()
    f = open('RULES.sha256').read().split()[0]
    if not (h == f == RULES_SHA): sys.exit(f'ABORT: rules hash mismatch ({h})')

def load():
    d = yf.download(ALL, start='2005-01-01', auto_adjust=True, progress=False)['Close'][ALL]
    first = pd.Timestamp(dt.date.today().replace(day=1))
    d = d[d.index < first]  # only fully closed months
    return d

def weights_at(d, t):
    """Target asset weights using data up to month-end t (inclusive)."""
    d = d[d.index <= t]; m = d.resample('ME').last(); R = m.pct_change(fill_method=None); D = d.pct_change(fill_method=None)
    # TSMOM sleeve weight history (for sleeve return backtest)
    sig = sum(np.sign(m/m.shift(l)-1) for l in (1, 3, 12))[TS]/3
    vol = (D[TS].rolling(63).std()*np.sqrt(252)).resample('ME').last()
    n = sig.notna().sum(axis=1).replace(0, np.nan)
    w = (sig*0.10/vol).div(np.sqrt(n), axis=0).clip(-1, 1); g = w.abs().sum(axis=1); w = w.div(np.maximum(g/2, 1), axis=0).fillna(0)
    ts_r = (w.shift(1)*R[TS].fillna(0)).sum(axis=1) - COST*w.diff().abs().sum(axis=1)
    qv_r = sum(R[k]*v for k, v in QV.items()); pw_r = sum(R[k]*v for k, v in PW.items())
    S = pd.DataFrame({'TSMOM': ts_r, 'QualVal': qv_r, 'PutWrite': pw_r}).dropna()
    S = S[S.index >= S.index[0] + pd.offsets.MonthEnd(13)]  # TSMOM needs 12m warmup
    iv = 1/S.rolling(36, min_periods=24).std(); sw = iv.div(iv.sum(axis=1), axis=0).clip(upper=CAP)
    book = (sw.shift(1)*S).sum(axis=1)[sw.shift(1).notna().all(axis=1)]
    bvol = book.rolling(12).std().iloc[-1]*np.sqrt(12); scale = min(1.0, VT/bvol)
    s = sw.iloc[-1]
    a = pd.Series(0.0, index=ALL)
    a[TS] += s['TSMOM']*w.iloc[-1][TS]
    for k, v in QV.items(): a[k] += s['QualVal']*v
    for k, v in PW.items(): a[k] += s['PutWrite']*v
    a *= scale
    meta = dict(sleeve_w=s.round(4).to_dict(), book_vol12=round(float(bvol), 4), overlay=round(float(scale), 4))
    return a, meta

def main():
    check_hash(); d = load(); me = d.resample('ME').last().index
    rows = pd.read_csv(LEDGER, parse_dates=['date']).to_dict('records') if os.path.exists(LEDGER) else []
    todo = [t for t in me if t >= START and (not rows or t > pd.Timestamp(rows[-1]['date']))]
    mpx = d.resample('ME').last()
    for t in todo:
        a, meta = weights_at(d, t); ret = np.nan; eq = 1.0; spy = np.nan
        if rows:
            prev = rows[-1]; pw = pd.Series(json.loads(prev['weights']))
            r = (mpx.loc[t]/mpx.loc[pd.Timestamp(prev['date'])]-1).reindex(pw.index).fillna(0)
            ret = float((pw*r).sum() - COST*(a.reindex(pw.index, fill_value=0)-pw).abs().sum())
            eq = prev['equity']*(1+ret); spy = float(mpx.loc[t, 'SPY']/mpx.loc[pd.Timestamp(prev['date']), 'SPY']-1)
        rows.append(dict(date=t.date(), paper_return=ret, spy_return=spy, equity=eq,
                         weights=json.dumps({k: round(v, 5) for k, v in a.items() if abs(v) > 1e-6}),
                         gross=round(a.abs().sum(), 4), net=round(a.sum(), 4), meta=json.dumps(meta)))
    L = pd.DataFrame(rows); L.to_csv(LEDGER, index=False)
    status(L)

def status(L):
    r = L['paper_return'].dropna(); n = len(r); last = L.iloc[-1]
    print(f"Rules v1 hash OK. Last positions as of {last['date']}: {last['weights']}  meta={last['meta']}")
    if n == 0: print('n=0 live months | return to date 0.00% | MDD 0.00% | verdict NOT_READY (awaiting first month-end)'); return
    eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min(); w = winrate(r); p = pf_boot(r)
    sp = L['spy_return'].dropna(); sh = lambda x: x.mean()/x.std()*np.sqrt(12) if len(x) > 1 and x.std() > 0 else np.nan
    kill = mdd < -0.15 or (n >= 24 and (p['PF'] < 1 or w['WR'] < 0.5 or sh(r) <= 0 or p['PF_boot_le1'] > 0.5))
    ready = n >= 100 and p['PF'] >= 1.5 and w['WR'] >= 0.5 and mdd >= -0.20
    v = 'KILL' if kill else ('READY' if ready else 'NOT_READY')
    print(f"n={n} | return to date {eq.iloc[-1]-1:+.2%} (SPY {(1+sp).prod()-1:+.2%}) | MDD {mdd:.2%} | WR {w['WR']:.0%} "
          f"[{w['WR_lo']:.0%},{w['WR_hi']:.0%}] p={w['binom_p']:.3f} | PF {p['PF']:.2f} [{p['PF_lo']:.2f},{p['PF_hi']:.2f}] P(PF<=1)={p['PF_boot_le1']:.2f} "
          f"| Sharpe {sh(r):.2f} vs SPY {sh(sp):.2f} | verdict {v}")

if __name__ == '__main__': main()
