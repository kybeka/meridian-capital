"""Revalidate the existing AMC protocol against the supplied Bloomberg snapshot."""
from pathlib import Path
from datetime import datetime
from itertools import product
import hashlib
import importlib.util
import json
import shutil

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from scipy.optimize import minimize

P = Path(__file__).resolve().parents[1]
RELEASE = P / 'Reference'
SOURCE = P / 'Data/Raw sources/AMC Bloomerg Data.xlsx'
A = ['SPY', 'VWO', 'EEMV', 'DBC', 'SCHD', 'VGSH', 'STIP']
HELD = ['SPY', 'EEMV', 'DBC', 'VGSH', 'SCHD', 'STIP']
for name in ['Data/Raw sources', 'Results', 'Source']:
    (P / name).mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
shutil.copy2(SOURCE, P / 'Source' / SOURCE.name)
sf = load_workbook(SOURCE, data_only=False, read_only=True).worksheets[0]
sv = load_workbook(SOURCE, data_only=True, read_only=True).worksheets[0]
rows = list(sv.values)
assert list(rows[0][1:8]) == [a + ' US Equity' for a in A]
assert len(rows[1:]) == 180
assert sv['A2'].value == '#NAME?'
actual_dates = pd.DatetimeIndex([datetime(2011, 10, 31)] + [r[0] for r in rows[2:]])
assert list(actual_dates.to_period('M')) == list(pd.period_range('2011-10', '2026-09', freq='M'))
prices = pd.DataFrame([r[1:8] for r in rows[1:]], index=actual_dates, columns=A).astype(float)
assert np.isfinite(prices.values).all() and (prices.values > 0).all()
prices.index.name = 'source_observation_date'
prices.to_csv(P / 'Data/bloomberg_source_prices.csv')
prices.index = prices.index.to_period('M').to_timestamp('M')
prices.index.name = 'month'
prices.to_csv(P / 'Data/month_end_prices.csv')
returns = prices.pct_change(fill_method=None).iloc[1:]
assert returns.shape == (179, 7) and returns.notna().all().all()
returns.to_csv(P / 'Data/monthly_returns.csv')
h = returns.loc['2021-10':'2026-09']
assert len(h) == 60
h.to_csv(P / 'Data/current_60_month_returns.csv')
metadata = {
    'source_workbook': str(SOURCE), 'source_sha256': source_hash,
    'first_date_correction': {'cell': 'Sheet1!A2', 'saved_value': '#NAME?',
        'confirmed_date': '2011-10-31', 'basis': 'User explicitly confirmed 31.10.2011 in this chat'},
    'visible_download_formula': sf['A2'].value,
    'adjustment_provenance': 'SPY formula explicitly requests normal/special dividend and capital-change adjustment. Other six columns contain saved values; their original request settings are not preserved in this workbook.',
    'source_dates': 'Actual observed dates retained separately; analysis dates normalized to calendar month-end without filling prices.',
    'risk_free_source': 'Existing independent FRED DGS1MO yield-accrual proxy, unchanged',
    'price_rows': len(prices), 'return_rows': len(returns),
}
(P / 'Data/source_metadata.json').write_text(json.dumps(metadata, indent=2))
v = h.cov().values * 12
mu = h.mean().values * 12
(h.cov() * 12).to_csv(P / 'Data/annual_covariance.csv')
h.corr().to_csv(P / 'Data/correlations.csv')
pd.DataFrame({'annual_mean_input': h.mean() * 12, 'annual_volatility': h.std() * np.sqrt(12)}).to_csv(P / 'Data/annual_inputs.csv')

def risk(w):
    return w * (v @ w) / (w @ v @ w)

def derivative(w):
    z = v @ w
    q = w @ z
    return (np.diag(z) + np.diag(w) @ v) / q - np.outer(w * z, 2 * z) / q ** 2

stocks = np.isin(np.arange(7), [0, 1, 2, 4]).astype(float)
groups = [([0, 4], .05), ([1, 2], .05), ([3], .05), ([5], .05), ([6], .05), ([5, 6], .20)]
cons = [
    {'type': 'eq', 'fun': lambda w: w.sum() - 1, 'jac': lambda w: np.ones(7)},
    {'type': 'eq', 'fun': lambda w: w @ v @ w / .0064 - 1, 'jac': lambda w: 2 * v @ w / .0064},
    {'type': 'ineq', 'fun': lambda w: .65 - stocks @ risk(w), 'jac': lambda w: -stocks @ derivative(w)},
    {'type': 'ineq', 'fun': lambda w: .4 - risk(w), 'jac': lambda w: -derivative(w)},
]
for ids, floor in groups:
    mask = np.isin(np.arange(7), ids).astype(float)
    cons.append({'type': 'ineq', 'fun': lambda w, m=mask, f=floor: m @ w - f, 'jac': lambda w, m=mask: m})
solutions = []
seed_results = []
for seed in [12, 91]:
    good = []
    for start in np.random.default_rng(seed).dirichlet(np.ones(7), 100):
        z = minimize(lambda w: -mu @ w, start, jac=lambda w: -mu,
            bounds=[(0, .35)] * 7, constraints=cons, method='SLSQP',
            options={'ftol': 1e-11, 'maxiter': 400})
        if (z.success and abs(z.x.sum() - 1) < 1e-7
                and abs(np.sqrt(z.x @ v @ z.x) - .08) < 1e-7
                and min(np.min(c['fun'](z.x)) for c in cons if c['type'] == 'ineq') >= -1e-7):
            good.append(z)
    assert good, ('No verified solution for seed', seed)
    seed_results.append({'seed': seed, 'starts': 100, 'verified_solutions': len(good),
        'best_annual_mean_objective': float(-min(z.fun for z in good))})
    solutions.extend(good)
exact = min(solutions, key=lambda z: z.fun).x
assert abs(seed_results[0]['best_annual_mean_objective'] - seed_results[1]['best_annual_mean_objective']) < 1e-7

def implementable(w):
    return (abs(w.sum() - 1) < 1e-12 and min(w) >= 0 and max(w) <= .35 + 1e-12
        and np.sqrt(w @ v @ w) <= .08 + 1e-10 and np.sqrt(w @ v @ w) >= .07
        and max(risk(w)) <= .4 + 1e-10 and stocks @ risk(w) <= .65 + 1e-10
        and all(w[ids].sum() >= floor - 1e-12 for ids, floor in groups))

rounded = np.round(exact, 4)
rounded[-1] = 1 - rounded[:-1].sum()
rounding = 'Nearest 0.01 percentage point, final STIP weight is the residual to 100%.'
if not implementable(rounded):
    lower = np.floor(exact * 10000) / 10000
    candidates = []
    for choices in product([0, 1], repeat=7):
        candidate = lower + np.array(choices) / 10000
        if implementable(candidate):
            candidates.append(candidate)
    assert candidates, 'No feasible adjacent rounding: review before producing implementable weights.'
    rounded = min(candidates, key=lambda w: np.sum((w - exact) ** 2))
    rounding = 'Nearest feasible floor/ceiling combination at 0.01 percentage point precision; all original limits checked.'
old = json.loads((RELEASE / 'Results/recommended_weights.json').read_text())['rounded_weights']
record = {'eligible_assets': A, 'excluded_asset': 'XLE', 'fit_months': 60,
    'fit_first': str(h.index[0].date()), 'fit_last': str(h.index[-1].date()),
    'exact_weights': dict(zip(A, exact)), 'rounded_weights': dict(zip(A, rounded)),
    'rounded_volatility': float(np.sqrt(rounded @ v @ rounded)),
    'rounded_risk_shares': dict(zip(A, risk(rounded))), 'rounding_method': rounding,
    'seed_results': seed_results, 'formal_global_optimum_proven': False}
(P / 'Results/recommended_weights.json').write_text(json.dumps(record, indent=2))
pd.DataFrame({'previous_weight': pd.Series(old), 'Bloomberg_exact_weight': pd.Series(dict(zip(A, exact))),
    'Bloomberg_rounded_weight': pd.Series(dict(zip(A, rounded))),
    'weight_change_percentage_points': (pd.Series(dict(zip(A, rounded))) - pd.Series(old)) * 100,
    'Bloomberg_rounded_risk_share': pd.Series(dict(zip(A, risk(rounded))))}).loc[A].to_csv(P / 'Results/allocation_comparison.csv')
print('Current optimizer completed:', record, flush=True)

# Reuse the recorded protocol unchanged against the new local Data directory.
assert {a for a, w in record['rounded_weights'].items() if w > 0} == set(HELD)
spec = importlib.util.spec_from_file_location('bloomberg_backtest', P / 'Code/backtest.py')
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
f = returns[HELD].loc['2016-11':]
cv = h[HELD].cov().values * 12
new_w = np.array([record['rounded_weights'][a] for a in HELD])
old_w = np.array([old[a] for a in HELD])
weights = {'Bloomberg reoptimized MVO': new_w, 'Existing weights on Bloomberg data': old_w,
    'Fixed equal weight': np.ones(6) / 6, 'Fixed risk parity': bt.parity(cv)}
results, series = bt.suite(weights, f)
series.to_csv(P / 'Results/main_monthly_returns.csv')
pd.DataFrame({name: z['statistics'] for name, z in results.items()}).T.to_csv(P / 'Results/backtest_summary.csv')
checkpoint = pd.DataFrame(index=HELD)
for label, name in [('MVO', 'Bloomberg reoptimized MVO'), ('Equal weight', 'Fixed equal weight'), ('Risk parity', 'Fixed risk parity')]:
    checkpoint[label + ' weight'] = weights[name]
    checkpoint[label + ' risk share'] = bt.risk(weights[name], cv)
checkpoint.to_csv(P / 'Results/checkpoint_2.csv')
current_risk = {name: {'estimated_volatility': float(np.sqrt(w @ cv @ w)),
    'normal_monthly_95pct_var': float(1.6448536269514722 * np.sqrt(w @ cv @ w) / np.sqrt(12)),
    'risk_shares': dict(zip(HELD, bt.risk(w, cv)))} for name, w in weights.items()}
original = pd.read_csv(RELEASE / 'Results/backtest_summary.csv', index_col=0)
comparison = pd.DataFrame({
    'Previous report on Yahoo': original.loc['Proposed fixed MVO'],
    'Same allocation on Bloomberg': pd.Series(results['Existing weights on Bloomberg data']['statistics']),
    'Reoptimized on Bloomberg': pd.Series(results['Bloomberg reoptimized MVO']['statistics']),
}).T
comparison.to_csv(P / 'Results/source_and_reoptimization_comparison.csv')

checks = 0
max_error = 0.0
for name, z in results.items():
    w = weights[name]
    holdings = np.zeros(6)
    nav = 100_000_000.0
    path = [nav]
    independent_returns = []
    for day, monthly in f.iterrows():
        before = nav
        traded = np.abs(before * w - holdings).sum()
        fee = .001 * traded
        holdings = (before - fee) * w * (1 + monthly.values)
        nav = holdings.sum()
        path.append(nav)
        independent_returns.append(nav / before - 1)
    x = pd.Series(independent_returns, index=f.index)
    err = float(np.max(np.abs(x.values - series[name].values)))
    assert err < 1e-12
    max_error = max(max_error, err)
    rf = bt.RF.reindex(x.index)
    vol = np.std(x.values, ddof=1) * np.sqrt(12)
    wealth = np.array(path)
    independent = {'cagr': (nav / 100_000_000) ** (12 / len(x)) - 1,
        'volatility': vol, 'sharpe': np.mean(x.values - rf.values) * 12 / vol,
        'max_month_end_drawdown': np.min(wealth / np.maximum.accumulate(wealth) - 1),
        'historical_one_month_95pct_var': -np.percentile(x.values, 5), 'terminal_value_usd': nav}
    for key, value in independent.items():
        assert abs(value - z['statistics'][key]) <= max(1e-10, abs(value) * 1e-11)
    checks += len(x)
assert max(abs(bt.risk(weights['Fixed risk parity'], cv) - 1 / 6)) < 1e-7
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
verification = {'passed': True, 'main_strategy_months_checked': checks,
    'independent_dollar_accounting_max_return_error': max_error,
    'all_current_policy_constraints_checked': True, 'source_workbook_unchanged': True,
    'original_release_unchanged': True, 'untouched_holdout': False}
(P / 'Results/verification.json').write_text(json.dumps(verification, indent=2))
(P / 'Results/main_results.json').write_text(json.dumps({'protocol': {'fit': 'October 2021–September 2026',
    'backtest': 'November 2016–September 2026, 119 months', 'rebalancing': 'Fixed targets restored monthly',
    'cost': '.001 per dollar bought or sold including inception', 'rf': 'Unchanged independent FRED DGS1MO proxy',
    'interpretation': 'Retrospective, no untouched historical selection holdout'},
    'current_risk': current_risk, 'strategies': results, 'verification': verification}, indent=2))
print(comparison[['cagr', 'volatility', 'sharpe', 'max_month_end_drawdown']].to_string(), flush=True)
print('Independent main backtest verification passed.', flush=True)
