from run import *
def overlay(r, tgt, lb=12):
    v = r.rolling(lb).std().shift(1)*np.sqrt(12); s = (tgt/v).clip(upper=1.0).fillna(1.0); return r*s
pre = comb[:'2015-12']
for t in [0.05,0.06,0.07,0.08,0.09,0.10]:
    p = perf(overlay(comb,t)[:'2015-12']); f = perf(overlay(comb,t)); print(t, 'pre', round(p['CAGR'],4), round(p['Sharpe'],2), round(p['MDD'],4), '| full', round(f['CAGR'],4), round(f['Sharpe'],2), round(f['MDD'],4))
print('none full', perf(comb))
