import numpy as np, pandas as pd, io, json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from edge_validator import *
P = pd.read_pickle('prices.pkl'); M = P.resample('ME').last(); R = M.pct_change(fill_method=None)
D = P.pct_change(fill_method=None)
# splice ETFs with older mutual-fund proxies (proxy returns used only before ETF exists)
SPL = {'SPY':'VFINX','TLT':'VUSTX','IEF':'VBMFX','LQD':'VBMFX','SHY':'FGOVX','HYG':'VWEHX','GLD':'FSAGX','VNQ':'VGSIX','DBC':'PCRIX'}
def splice(df):
    out = {}
    for t in ['SPY','EFA','EEM','IWM','TLT','IEF','SHY','LQD','HYG','TIP','GLD','DBC','USO','SLV','VNQ']:
        s = df[t].copy()
        if t in SPL: s = s.combine_first(df[SPL[t]].where(df[t].isna()))
        out[t] = s
    return pd.DataFrame(out)
RM, RD = splice(R), splice(D)
RM = RM[RM.index >= '1986-01-01']; RM.iloc[:, :] = RM.where(RM.abs() < 1)  # guard
COST = 0.001
def tsmom(lbs=(1,3,12), tgt=0.10, R=RM, RD=RD):
    px = (1+R.fillna(0)).cumprod().where(R.notna())
    sig = sum(np.sign(px/px.shift(l)-1) for l in lbs)/len(lbs)
    vol = RD.rolling(63).std().resample('ME').last().reindex(R.index)*np.sqrt(252)
    navail = sig.notna().sum(axis=1).replace(0, np.nan)
    w = (sig*tgt/vol).div(np.sqrt(navail), axis=0)  # ~tgt portfolio vol if assets uncorrelated
    w = w.clip(-1, 1); g = w.abs().sum(axis=1); w = w.div(np.maximum(g/2.0, 1), axis=0)  # gross cap 200%
    w = w.fillna(0); ret = (w.shift(1)*R.fillna(0)).sum(axis=1) - COST*w.diff().abs().sum(axis=1)
    return ret[w.shift(1).abs().sum(axis=1) > 0], w
# ---- walk-forward variant selection (pre-2015 fit, 12m embargo, test 2016+) ----
grid = [(l, t) for l in [(1,), (3,), (12,), (1,3,12), (3,12), (6,12)] for t in [0.08, 0.10, 0.12]]
srs = {}; 
for l, t in grid:
    r, _ = tsmom(l, t); srs[(l, t)] = r
IS = {k: v[:'2014-12'].mean()/v[:'2014-12'].std() for k, v in srs.items()}
best = max(IS, key=IS.get); sr_var = np.var(list(IS.values()))
tm, W = tsmom((1,3,12), 0.10)  # pre-registered spec from plan (reported as main)
wf = srs[best]['2016-01':]
# ---- quality/value long-only proxy (Ken French, VW top-30% OP + top-30% B/M) ----
def ff(fn, col):
    txt = open(fn).read().split('\n'); i = [j for j, x in enumerate(txt) if 'Value Weight Returns -- Monthly' in x][0]
    rows = []
    for x in txt[i+2:]:
        if not x.strip() or not x.strip()[0].isdigit(): break
        rows.append(x)
    df = pd.read_csv(io.StringIO(txt[i+1]+'\n'+'\n'.join(rows)), index_col=0)
    df.index = pd.to_datetime(df.index.astype(str), format='%Y%m')+pd.offsets.MonthEnd(0)
    return df[col].astype(float)/100
qv = 0.5*ff('Portfolios_Formed_on_OP.csv', 'Hi 30')+0.5*ff('Portfolios_Formed_on_BE-ME.csv', 'Hi 30') - 0.002/12
qv = qv['1986-01':]
etf = R[['QUAL','VLUE','MTUM','USMV']].dropna().mean(axis=1) - 0.0015/12
# ---- VRP: CBOE PUT index (cash-secured S&P put write) ----
vrp = R['^PUT'].dropna(); vrp = vrp[vrp.abs() < 0.5]
spy = RM['SPY'].dropna()
# ---- combined inverse-vol book, 40% cap, residual cash (0%) ----
S = pd.DataFrame({'TSMOM': tm, 'QualVal': qv, 'PutWrite': vrp})
iv = 1/S.rolling(36, min_periods=24).std().shift(1); w = iv.div(iv.sum(axis=1), axis=0).clip(upper=0.40)
comb = (w*S).sum(axis=1)[w.notna().any(axis=1) & (w.sum(axis=1) > 0)]
# ---- coin-flip control: random long/short SPY each month ----
coin = spy*np.where(np.random.default_rng(7).random(len(spy)) < 0.5, 1, -1) - COST*2
# ---- random-entry permutation MC ----
def perm_tsmom(B=500):
    rng = np.random.default_rng(1); out = []
    Wv = W.shift(1).values; Rv = RM.fillna(0).values
    for _ in range(B):
        sgn = rng.choice([-1, 1], size=Wv.shape); r = np.nansum(np.abs(Wv)*sgn*Rv, axis=1)
        r = pd.Series(r, RM.index)[tm.index]; out.append(r.mean()/r.std())
    return np.array(out)
def active_signflip(r, b, B=5000):
    a = (r-b).dropna(); rng = np.random.default_rng(2); m = a.mean()
    sims = np.array([(a.values*rng.choice([-1, 1], len(a))).mean() for _ in range(B)]); return (sims < m).mean()
pt = perm_tsmom(); mc = {'TSMOM': (pt < tm.mean()/tm.std()).mean(),
     'QualVal (active vs mkt)': active_signflip(qv, spy), 'PutWrite (active vs SPY)': active_signflip(vrp, spy),
     'Combined (active vs SPY)': active_signflip(comb, spy), 'CoinFlip (active vs SPY)': active_signflip(coin, spy)}
rows = {'SPY buy&hold': full_report(spy), 'TSMOM 1/3/12 10%vol (pre-reg)': full_report(tm, len(grid), sr_var),
        f'TSMOM WF OOS 2016+ (picked {best})': full_report(wf, len(grid), sr_var),
        'QualVal (FF hi-OP+hi-BM)': full_report(qv), 'Factor ETF blend 2013+': full_report(etf),
        'PutWrite (CBOE PUT)': full_report(vrp), 'Combined inv-vol book': full_report(comb, len(grid), sr_var),
        'Coin-flip control': full_report(coin)}
T = pd.DataFrame(rows).T
# same-date SPY comparisons
for name, r in [('TSMOM', tm), ('QualVal', qv), ('PutWrite', vrp), ('Combined', comb), ('ETFblend', etf), ('WF_OOS', wf)]:
    b = spy.reindex(r.index).dropna(); p = perf(b); print(f'SPY same dates as {name}: CAGR {p["CAGR"]:.3f} Sharpe {p["Sharpe"]:.2f} MDD {p["MDD"]:.3f}')
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
T.to_csv('results.csv'); print(T.to_string()); print('MC percentiles', mc); print('IS best', best, IS[best]); print('corr', S.corr().round(2).to_dict())
json.dump({'mc': mc, 'best': str(best)}, open('mc.json', 'w'))
fig, ax = plt.subplots(figsize=(12, 6.5))
for nm, r in [('SPY (VFINX-spliced)', spy), ('TSMOM', tm), ('Quality/Value', qv), ('PutWrite', vrp), ('Combined', comb), ('Coin flip', coin)]:
    ax.plot((1+r.dropna()).cumprod(), label=nm, lw=2 if nm == 'Combined' else 1.2)
ax.set_yscale('log'); ax.legend(); ax.grid(alpha=.3); ax.set_title('Growth of $1 (log), monthly, net of modeled costs'); plt.tight_layout(); plt.savefig('equity_curves.png', dpi=130)
