"""Check the Round 1 page against a fresh Bloomberg revalidation directory."""
import sys
import json
from pathlib import Path
from html.parser import HTMLParser
import numpy as np
import pandas as pd

run = Path(sys.argv[1])
site = Path(__file__).resolve().parents[1] / 'dist'
results = json.loads((run / 'Results/main_results.json').read_text())
strategy = results['strategies']['Existing weights on Bloomberg data']
weights = pd.Series(strategy['weights'])
prices = pd.read_csv(run / 'Data/month_end_prices.csv', index_col=0, parse_dates=True)
returns = prices.pct_change(fill_method=None).iloc[1:]
training = returns.loc['2021-10':'2026-09', weights.index]
assert len(training) == 60
covariance = np.cov(training.to_numpy(), rowvar=False, ddof=1) * 12
w = weights.to_numpy()
variance = w @ covariance @ w
risk = pd.Series(w * (covariance @ w) / variance, index=weights.index)
volatility = float(np.sqrt(variance))
checks = {
    'weights_sum_to_one': abs(w.sum() - 1) < 1e-12,
    'long_only_and_35pct_cap': bool((w >= 0).all() and (w <= .35).all()),
    'volatility_in_band_and_at_target': .07 <= volatility <= .08 + 1e-10,
    'single_risk_cap': bool((risk <= .4 + 1e-10).all()),
    'equity_risk_cap': risk[['SPY', 'SCHD', 'EEMV']].sum() <= .65,
    'us_equity_floor': weights[['SPY', 'SCHD']].sum() >= .05,
    'em_equity_floor': weights['EEMV'] >= .05,
    'asset_floors': bool((weights[['DBC', 'VGSH', 'STIP']] >= .05).all()),
    'bond_floor': weights[['VGSH', 'STIP']].sum() >= .20,
    'main_accounting_verification': results['verification']['passed'],
}
assert all(checks.values()), checks
class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.charts = []
        self.table = None
        self.rows = {'allocation-table': [], 'backtest-table': []}
        self.row = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('class') == 'allocation-row':
            self.charts.append((a['data-capital'], a['data-risk']))
        if tag == 'table':
            self.table = a.get('class')
        if tag == 'tr':
            self.row = []
    def handle_data(self, data):
        self.text.append(data)
        if self.table in self.rows:
            self.row.append(data)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.table in self.rows:
            self.rows[self.table].append(self.row)
        if tag == 'table':
            self.table = None
page = Page()
page.feed((site / 'round-1.html').read_text())
order = ['SPY', 'EEMV', 'DBC', 'SCHD', 'VGSH', 'STIP']
percent = lambda x: f'{x * 100:.2f}'
assert page.charts == [(percent(weights[a]), percent(risk[a])) for a in order]
assert len(page.rows['allocation-table']) == 8
assert len(page.rows['backtest-table']) == 4
for row, asset in zip(page.rows['allocation-table'][1:-1], order):
    assert row[0] == asset
    assert row[-2:] == [percent(weights[asset])+'%', percent(risk[asset])+'%']
summary = pd.read_csv(run / 'Results/backtest_summary.csv', index_col=0)
names = ['Existing weights on Bloomberg data', 'Fixed equal weight', 'Fixed risk parity']
for row, name in zip(page.rows['backtest-table'][1:], names):
    s = summary.loc[name]
    expected = [percent(s.cagr)+'%', percent(s.volatility)+'%', f'{s.sharpe:.3f}', (percent(s.max_month_end_drawdown)+'%').replace('-', '−')]
    assert row[1:] == expected, (row, expected)
text = ' '.join(page.text)
assert percent(volatility)+'%' in text
assert percent(weights[['VGSH', 'STIP']].sum())+'%' in text
assert percent(strategy['statistics']['historical_one_month_95pct_var'])+'%' in text
assert percent(1.6448536269514722 * volatility / np.sqrt(12))+'%' in text
assert strategy['statistics']['months'] == 119
assert '119 monthly returns' in text and 'November 2016–September 2026' in text
assert '14 October 2026' not in text and '17 October 2026' not in text
checks['displayed_numbers_match_fresh_results'] = True
report = {
    'passed': True,
    'checks': {key: bool(value) for key, value in checks.items()},
    'sources': 'Supplied Bloomberg ETF workbook; FRED DGS1MO prior-month yield-accrual proxy',
    'fit_period': 'October 2021–September 2026',
    'backtest_period': 'November 2016–September 2026',
    'source_workbook_sha256': json.loads((run / 'Data/source_metadata.json').read_text())['source_sha256'],
    'agreed_weights': weights.to_dict(),
    'estimated_risk_shares': risk.to_dict(),
    'estimated_annual_volatility': volatility,
    'historical_monthly_95pct_var': strategy['statistics']['historical_one_month_95pct_var'],
    'current_normal_monthly_95pct_var': float(1.6448536269514722 * volatility / np.sqrt(12)),
    'main_verification': results['verification'],
    'untouched_holdout': False,
}
(run / 'website-verification.json').write_text(json.dumps(report, indent=2)+'\n')
summary.loc[names].rename(index={'Existing weights on Bloomberg data':'Agreed MVO'}).to_csv(site / 'research/round-1-results.csv')
print('PASS: agreed allocation constraints, 24 allocation/chart values, 12 backtest metrics, volatility, bond weight, both VaR figures and sample periods.')
