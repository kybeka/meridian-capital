"""Standalone sensitivity analysis; does not edit Excel, reports, or source files."""
from pathlib import Path
from itertools import product
import json
import hashlib
import shutil
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1]
(ROOT / 'Data').mkdir(exist_ok=True)
(ROOT / 'Results').mkdir(exist_ok=True)
FILES = ['current_60_month_returns.csv', 'monthly_returns.csv', 'risk_free_monthly.csv']
hashes = {}
for name in FILES:
    src = SOURCE / 'Data' / name
    hashes[name] = hashlib.sha256(src.read_bytes()).hexdigest()
    shutil.copy2(src, ROOT / 'Data' / name)
A = ['SPY', 'VWO', 'EEMV', 'DBC', 'SCHD', 'VGSH', 'STIP']
h = pd.read_csv(ROOT / 'Data/current_60_month_returns.csv', index_col=0)[A]
assert len(h) == 60
v = h.cov().values * 12
mu = h.mean().values * 12
old = json.loads((SOURCE / 'Results/recommended_weights.json').read_text())
basew = np.array([old['exact_weights'][a] for a in A])
stocks = np.array([1, 1, 1, 0, 1, 0, 0])
BASE = dict(risk_cap=.40, floor=.05, bonds=.20, capital_cap=.35, stock_risk=.65)
groups = [[0, 4], [1, 2], [3], [5], [6]]

def risk(w):
    return w * (v @ w) / (w @ v @ w)

def derivative(w):
    z = v @ w
    q = w @ z
    return (np.diag(z) + np.diag(w) @ v) / q - np.outer(w * z, 2 * z) / q**2

def margins(w, p):
    rc = risk(w)
    return np.r_[w, p['capital_cap'] - w, p['risk_cap'] - rc,
                 p['stock_risk'] - stocks @ rc,
                 [w[g].sum() - p.get('floor_' + str(i), p['floor']) for i, g in enumerate(groups)],
                 w[5:7].sum() - p['bonds']]

def solve(p):
    cs = [dict(type='eq', fun=lambda w: w.sum()-1, jac=lambda w: np.ones(7)),
          dict(type='eq', fun=lambda w: (w @ v @ w)/.0064-1, jac=lambda w: 2*v@w/.0064),
          dict(type='ineq', fun=lambda w: p['risk_cap']-risk(w), jac=lambda w: -derivative(w)),
          dict(type='ineq', fun=lambda w: p['stock_risk']-stocks@risk(w), jac=lambda w: -stocks@derivative(w))]
    for i, g in enumerate(groups + [[5, 6]]):
        m = np.isin(np.arange(7), g).astype(float)
        floor = p.get('floor_' + str(i), p['floor']) if i < 5 else p['bonds']
        cs.append(dict(type='ineq', fun=lambda w, m=m, f=floor: m@w-f, jac=lambda w, m=m: m))
    bests = []
    counts = []
    for seed in [17, 83]:
        good = []
        starts = [basew, np.ones(7)/7] + list(np.random.default_rng(seed).dirichlet(np.ones(7), 22))
        for x in starts:
            z = minimize(lambda w: -mu@w, x, jac=lambda w: -mu, method='SLSQP',
                         bounds=[(0, p['capital_cap'])]*7, constraints=cs,
                         options=dict(ftol=1e-11, maxiter=500))
            if z.success and abs(z.x.sum()-1)<1e-7 and abs(np.sqrt(z.x@v@z.x)-.08)<1e-7 and margins(z.x,p).min()>=-1e-7:
                good.append(z)
        counts.append(len(good))
        if good:
            bests.append(min(good, key=lambda z:z.fun))
    if not bests:
        return None, counts, None
    best = min(bests, key=lambda z:z.fun)
    gap = max(z.fun for z in bests)-min(z.fun for z in bests) if len(bests)==2 else None
    return best.x, counts, gap

cases = [('Baseline', 'baseline', BASE.copy())]
def add(name, kind, **changes):
    cases.append((name, kind, BASE | changes))
for key, vals in [('risk_cap',[.35,.375,.425,.45]), ('floor',[.025,.075]),
                  ('bonds',[.15,.25,.30]), ('capital_cap',[.30,.325,.375,.40]),
                  ('stock_risk',[.55,.60,.70,.75])]:
    for val in vals:
        add(f'{key}={val:.3f}', 'one_limit', **{key:val})
for i, label in enumerate(['US','EM','commodities','VGSH','STIP']):
    for val in [.025,.075]:
        add(f'{label} minimum={val:.3f}', 'individual_floor', **{'floor_'+str(i):val})
for rc, fl, cap, sr in product([.35,.40,.45],[.025,.05,.075],[.30,.35,.40],[.60,.65,.70]):
    p = BASE | dict(risk_cap=rc, floor=fl, capital_cap=cap, stock_risk=sr)
    if p != BASE:
        cases.append((f'Joint {len(cases)}', 'joint', p))
rows = []
solutions = []
for n,(name,kind,p) in enumerate(cases):
    w, counts, gap = solve(p)
    r = dict(scenario=name, kind=kind, **p, feasible_solution_found=w is not None,
             verified_seed17=counts[0], verified_seed83=counts[1], seed_objective_gap=gap)
    if w is not None:
        # Independent risk calculation directly from monthly portfolio returns.
        portfolio = h.values@w
        q = np.var(portfolio,ddof=1)*12
        independent_rc = np.array([w[i]*np.cov(h.values[:,i],portfolio,ddof=1)[0,1]*12/q for i in range(7)])
        assert np.max(abs(independent_rc-risk(w)))<1e-10
        assert abs(q-.0064)<2e-8 and margins(w,p).min()>-1e-7
        r.update({a:float(w[i]) for i,a in enumerate(A)})
        r.update({a+'_risk':float(risk(w)[i]) for i,a in enumerate(A)})
        r.update(estimated_mean=float(mu@w), estimated_volatility=float(np.sqrt(q)),
                 max_weight_change_pp=float(np.max(abs(w-basew))*100),
                 reallocated_capital_pct=float(np.abs(w-basew).sum()/2*100),
                 bonds_weight=float(w[5:7].sum()), stock_risk_actual=float(stocks@risk(w)),
                 minimum_constraint_margin=float(margins(w,p).min()))
        solutions.append((name,w))
    rows.append(r)
    if n%10==0:
        print(f'Completed {n+1}/{len(cases)}', flush=True)
result = pd.DataFrame(rows)
result.to_csv(ROOT/'Results/scenarios.csv',index=False)
result[result.kind!='joint'].to_csv(ROOT/'Results/one_limit_results.csv',index=False)
# Same retrospective period and cost convention; never used to select the limits.
ret = pd.read_csv(ROOT/'Data/monthly_returns.csv',index_col=0,parse_dates=True)[A].loc['2016-11':]
rf = pd.read_csv(ROOT/'Data/risk_free_monthly.csv',index_col=0,parse_dates=True).monthly_rf_proxy.reindex(ret.index)
assert rf.notna().all()
bt = []
for name,w in solutions:
    wealth=1.; peak=1.; dd=0.; prev=None; net=[]
    for x in ret.values:
        turnover=float(w.sum()) if prev is None else float(abs(w-prev).sum())
        gross=float(x@w)
        monthly=(1-.001*turnover)*(1+gross)-1
        net.append(monthly); wealth*=1+monthly; peak=max(peak,wealth); dd=min(dd,wealth/peak-1)
        prev=w*(1+x)/(1+gross)
    x=np.array(net); vol=x.std(ddof=1)*np.sqrt(12)
    bt.append(dict(scenario=name,cagr=wealth**(12/len(x))-1,volatility=vol,
                   sharpe=float((x-rf.values).mean()*12/vol),drawdown=dd,
                   historical_var=-float(np.percentile(x,5))))
pd.DataFrame(bt).to_csv(ROOT/'Results/retrospective_context.csv',index=False)
assert all(hashlib.sha256((SOURCE/'Data'/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
metadata=dict(source_hashes=hashes,scenarios=len(cases),starts_per_scenario=48,
              fixed_target_volatility=.08,fit='October 2021–September 2026',
              source_files_unchanged=True,shared_excel_and_report_untouched=True,
              formal_global_optimum_proven=False,
              retrospective_results_not_used_to_select_limits=True)
(ROOT/'Results/verification.json').write_text(json.dumps(metadata,indent=2))
print(result[result.kind!='joint'][['scenario','SPY','EEMV','DBC','SCHD','VGSH','STIP','max_weight_change_pp','reallocated_capital_pct']].to_string(index=False),flush=True)
