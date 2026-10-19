from run import *
for nm, r in [('TSMOM prereg 2016+', tm['2016':]), ('Combined 2016+', comb['2016':]), ('SPY 2016+', spy['2016':])]:
    d = full_report(r); print(nm, {k: round(d[k], 3) for k in ['CAGR','vol','Sharpe','MDD','WR','WR_lo','binom_p','PF','PF_lo','PF_boot_le1']}, d['verdict'])
print('TSMOM 2008', (1+tm['2008']).prod()-1, 'SPY 2008', (1+spy['2008']).prod()-1, 'Comb 2008', (1+comb['2008']).prod()-1)
