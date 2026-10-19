"""Statistical gates for monthly return series (equivalent of the user's edge_validator.py)."""
import numpy as np, pandas as pd
from scipy import stats
RNG = np.random.default_rng(42)

def perf(r, ppy=12):
    r = pd.Series(r).dropna(); eq = (1+r).cumprod()
    yrs = len(r)/ppy; cagr = eq.iloc[-1]**(1/yrs)-1
    vol = r.std()*np.sqrt(ppy); sh = r.mean()/r.std()*np.sqrt(ppy) if r.std()>0 else 0
    mdd = (eq/eq.cummax()-1).min()
    return dict(start=str(r.index[0].date()), end=str(r.index[-1].date()), n=len(r),
                CAGR=cagr, vol=vol, Sharpe=sh, MDD=mdd)

def wilson(k, n, z=1.96):
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h, c+h

def winrate(r):
    r = pd.Series(r).dropna(); n = len(r); k = int((r > 0).sum())
    lo, hi = wilson(k, n)
    p = stats.binomtest(k, n, 0.5, alternative='greater').pvalue
    return dict(WR=k/n, WR_lo=lo, WR_hi=hi, binom_p=p, WR_label='insufficient sample' if n < 20 else '')

def pf(r):
    r = np.asarray(r); g = r[r > 0].sum(); l = -r[r < 0].sum(); return g/l if l > 0 else np.inf

def pf_boot(r, B=5000):
    r = np.asarray(pd.Series(r).dropna()); idx = RNG.integers(0, len(r), (B, len(r)))
    b = np.array([pf(r[i]) for i in idx])
    return dict(PF=pf(r), PF_lo=np.percentile(b, 2.5), PF_hi=np.percentile(b, 97.5), PF_boot_le1=(b <= 1).mean())

def block_boot_mdd(r, B=2000, block=12):
    r = np.asarray(pd.Series(r).dropna()); n = len(r); out = []
    for _ in range(B):
        starts = RNG.integers(0, n-block, n//block+1)
        s = np.concatenate([r[a:a+block] for a in starts])[:n]
        eq = np.cumprod(1+s); out.append((eq/np.maximum.accumulate(eq)-1).min())
    out = np.array(out)
    return dict(MDD_boot_med=np.median(out), MDD_boot_p05=np.percentile(out, 5), P_MDD_gt20=(out < -0.20).mean())

def psr(r, sr_star=0.0):
    """Probabilistic Sharpe (per-period SR), Bailey & Lopez de Prado."""
    r = pd.Series(r).dropna(); n = len(r); sr = r.mean()/r.std()
    g3 = stats.skew(r); g4 = stats.kurtosis(r, fisher=False)
    z = (sr-sr_star)*np.sqrt(n-1)/np.sqrt(1-g3*sr+(g4-1)/4*sr*sr)
    return stats.norm.cdf(z)

def dsr(r, n_trials, sr_trials_var):
    """Deflated Sharpe: PSR against expected max SR of n_trials (per-period units)."""
    if n_trials <= 1: return psr(r)
    em = 0.5772156649
    sr0 = np.sqrt(sr_trials_var)*((1-em)*stats.norm.ppf(1-1/n_trials)+em*stats.norm.ppf(1-1/(n_trials*np.e)))
    return psr(r, sr0)

def gate(pfv, wr, mdd, n):
    checks = {'n>=100': n >= 100, 'PF>=1.5': pfv >= 1.5, 'WR>=50%': wr >= 0.5, 'MDD<=20%': mdd >= -0.20}
    return checks, ('READY' if all(checks.values()) else 'NOT_READY')

def full_report(r, n_trials=1, sr_var=0.0):
    r = pd.Series(r).dropna(); d = perf(r); d.update(winrate(r)); d.update(pf_boot(r))
    d.update(block_boot_mdd(r)); d['PSR'] = psr(r); d['DSR'] = dsr(r, n_trials, sr_var); d['n_trials'] = n_trials
    c, v = gate(d['PF'], d['WR'], d['MDD'], d['n']); d.update({k: ('PASS' if x else 'FAIL') for k, x in c.items()}); d['verdict'] = v
    return d
