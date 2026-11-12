"""Reproduce the 10 November beta and discount-rate checks from archived inputs."""

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import t as student_t

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1]
PEER_PRICES = SOURCE / 'data/post-submission/peer_prices'
sys.path.insert(0, str(SOURCE / 'code'))
import portfolio_inputs as pi
import valuation as valuation

peer_manifest = json.loads((SOURCE / 'data/post-submission/peer_price_manifest.json').read_text())
for file in peer_manifest['files']:
    path = SOURCE / file['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != file['sha256']:
        raise ValueError(f"Archived peer price file has changed: {file['path']}")

STOCKS = ['ADBE', 'KR', 'HRL', 'BMY', 'XOM', 'HPQ']
inputs = {r['ticker']: r for r in json.loads((SOURCE / 'results/valuation/inputs.json').read_text())}
recorded = pd.read_csv(SOURCE / 'results/valuation/valuations.csv').set_index('ticker')
recorded_sensitivities = pd.read_csv(SOURCE / 'results/valuation/sensitivities.csv').set_index(['ticker', 'scenario'])
prices, daily, monthly, excess = pi.data(valuation.STOCKS)
sample = excess.tail(60)
rates = pd.read_csv(SOURCE / 'data/fred_history.csv', index_col=0, parse_dates=True).DGS1MO
peer_sets = json.loads((SOURCE / 'data/peer_sets.json').read_text())


def regression(y, x):
    pair = pd.concat([pd.Series(y, name='y'), pd.Series(x, name='x')], axis=1).dropna()
    y, x = pair.y.to_numpy(), pair.x.to_numpy()
    n = len(x)
    design = np.column_stack([np.ones(n), x])
    inverse = np.linalg.inv(design.T @ design)
    intercept, beta = inverse @ design.T @ y
    residuals = y - design @ np.array([intercept, beta])
    standard_error = np.sqrt((residuals @ residuals) / (n - 2) * inverse[1, 1])
    scores = design * residuals[:, None]
    meat = scores.T @ scores
    for lag in range(1, 4):
        cross = scores[lag:].T @ scores[:-lag]
        meat += (1 - lag / 4) * (cross + cross.T)
    hac_cov = inverse @ meat @ inverse * n / (n - 2)
    hac_se = np.sqrt(max(hac_cov[1, 1], 0))
    critical = student_t.ppf(.975, n - 2)
    return {
        'observations': n, 'beta': float(beta),
        'correlation': float(np.corrcoef(y, x)[0, 1]),
        'r_squared': float(np.corrcoef(y, x)[0, 1] ** 2),
        'standard_error_ols': float(standard_error),
        'beta_95_lower_ols': float(beta - critical * standard_error),
        'beta_95_upper_ols': float(beta + critical * standard_error),
        'standard_error_hac3': float(hac_se),
        'beta_95_lower_hac3': float(beta - critical * hac_se),
        'beta_95_upper_hac3': float(beta + critical * hac_se),
    }


def peer_monthly(ticker):
    if (SOURCE / 'data/prices' / f'{ticker}.json').exists():
        series = pi.prices(ticker).adjclose
    else:
        path = PEER_PRICES / f'{ticker}.json'
        raw = json.loads(path.read_text())['chart']['result'][0]
        assert raw['meta']['symbol'] == ticker
        dates = pd.to_datetime(raw['timestamp'], unit='s', utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
        series = pd.Series(raw['indicators']['adjclose'][0]['adjclose'], index=dates).dropna()
    returns = series.loc[:'2026-10-31'].resample('ME').last().pct_change(fill_method=None)
    return returns.reindex(sample.index) - rates.resample('ME').mean().reindex(sample.index) / 1200


betas, sensitivities, peers = [], [], []
for ticker in STOCKS:
    a = inputs[ticker]
    diagnostic = {'ticker': ticker, **regression(sample[ticker], sample.SPY)}
    np.testing.assert_allclose(diagnostic['beta'], a['beta_market'], rtol=1e-9)
    diagnostic['beta_saa'] = regression(sample[ticker], sample[pi.ETFS].dot(pi.SAA))['beta']
    for label, data in [('first30', sample.iloc[:30]), ('last30', sample.iloc[30:]),
                        ('last36', sample.tail(36)), ('last24', sample.tail(24))]:
        diagnostic[f'beta_{label}'] = regression(data[ticker], data.SPY)['beta']
    day_excess = daily.tail(252).sub(rates.reindex(daily.tail(252).index).ffill() / 25200, axis=0)
    diagnostic['beta_daily252'] = regression(day_excess[ticker], day_excess.SPY)['beta']
    weeks = prices.loc[:'2026-10-31'].resample('W-FRI').last().pct_change(fill_method=None)
    week_excess = weeks.sub(rates.resample('W-FRI').mean().reindex(weeks.index) / 5200, axis=0)
    week_excess = week_excess.loc['2021-11-01':'2026-10-31']
    diagnostic['beta_weekly_same_period'] = regression(week_excess[ticker], week_excess.SPY)['beta']
    base = valuation.fcff_value(a)
    np.testing.assert_allclose(base['value'], recorded.loc[ticker, 'dcf_value'], rtol=1e-10)
    shift = brentq(lambda delta: valuation.fcff_value(a, k_shift=delta)['value'] - a['price'], 0, .2)
    break_even = valuation.fcff_value(a, k_shift=shift)
    diagnostic.update(
        price=a['price'], k=base['k'], wacc=base['wacc'], cash_value=base['value'],
        terminal_share=base['terminal_share'], break_even_equity_rate_increase=shift,
        break_even_wacc=break_even['wacc'],
        break_even_market_beta=(base['k'] + shift - pi.POLICY['rf10y']) / pi.POLICY['erp'],
    )
    for label, kwargs in [('Base', {}), ('Equity rate +1pp', {'k_shift': .01}),
                          ('Equity rate +2pp', {'k_shift': .02})]:
        model = valuation.fcff_value(a, **kwargs)
        saved_label = label.replace('Equity rate +', 'Cost equity plus ')
        np.testing.assert_allclose(model['value'], recorded_sensitivities.loc[(ticker, saved_label), 'dcf_value'], rtol=1e-10)
        sensitivities.append(dict(ticker=ticker, scenario=label, market_beta_assumption=(model['k']-pi.POLICY['rf10y'])/pi.POLICY['erp'],
                                  cost_equity=model['k'], wacc=model['wacc'], cash_value=model['value'], price=a['price'], upside=model['value']/a['price']-1))
    adjusted_beta = (2 / 3) * a['beta_market'] + 1 / 3
    adjusted = dict(a, k=pi.POLICY['rf10y'] + adjusted_beta*pi.POLICY['erp'])
    model = valuation.fcff_value(adjusted)
    sensitivities.append(dict(ticker=ticker, scenario='Illustrative one-third beta shrinkage toward 1', market_beta_assumption=adjusted_beta,
                              cost_equity=model['k'], wacc=model['wacc'], cash_value=model['value'], price=a['price'], upside=model['value']/a['price']-1))
    for peer in peer_sets[ticker]:
        result = regression(peer_monthly(peer), sample.SPY)
        assert result['observations'] == 60, (ticker, peer, result['observations'])
        peers.append(dict(subject=ticker, peer=peer, **result))
    peer_beta = float(np.median([row['beta'] for row in peers if row['subject'] == ticker]))
    diagnostic['peer_median_raw_equity_beta'] = peer_beta
    peer_input = dict(a, k=pi.POLICY['rf10y'] + peer_beta*pi.POLICY['erp'])
    model = valuation.fcff_value(peer_input)
    sensitivities.append(dict(ticker=ticker, scenario='Raw peer equity beta median diagnostic only', market_beta_assumption=peer_beta,
                              cost_equity=model['k'], wacc=model['wacc'], cash_value=model['value'], price=a['price'], upside=model['value']/a['price']-1))
    betas.append(diagnostic)

pd.DataFrame(betas).to_csv(HERE / 'beta_diagnostics.csv', index=False)
pd.DataFrame(sensitivities).to_csv(HERE / 'discount_rate_scenarios.csv', index=False)
pd.DataFrame(peers).to_csv(HERE / 'peer_beta_diagnostics.csv', index=False)
metadata = {
    'valuation_date': '2026-11-06', 'audit_date': '2026-11-10',
    'monthly_sample': [str(sample.index[0].date()), str(sample.index[-1].date())],
    'source_root': 'research/round-2',
    'extra_peer_prices': PEER_PRICES.relative_to(SOURCE).as_posix(),
    'all_six_recorded_market_betas_and_base_cash_values_reproduced': True,
    'all_eighteen_recorded_base_and_equity_rate_scenarios_reproduced': True,
    'all_nineteen_peer_regressions_have_sixty_observations': True,
    'interpretation': [
        'Beta uncertainty intervals are historical regression diagnostics, not confidence intervals for future fair value.',
        'Rate shocks, shrinkage and raw peer medians are sensitivity scenarios, not validated replacement discount rates.',
        'Raw peer equity betas are not adjusted for leverage, cash holdings or business mix and are not bottom-up betas.',
        'Daily252 changes both frequency and lookback; weekly uses approximately the same calendar period as the monthly regression.',
        'Each cash valuation holds starting FCFF, growth, debt cost and balances unchanged while changing the equity hurdle and recalculating WACC.',
        'No submitted workbook, report, notebook or holdings have been changed.',
    ],
    'source_sha256': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() for name in [
        'results/valuation/inputs.json', 'results/valuation/valuations.csv',
        'results/valuation/sensitivities.csv', 'data/policies/valuation_policy_v4.json',
        'data/input_manifest.json', 'data/fred_history.csv', 'data/peer_sets.json',
        'data/post-submission/peer_price_manifest.json',
    ]},
}
(HERE / 'audit_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(pd.DataFrame(betas)[['ticker','beta','standard_error_ols','standard_error_hac3','beta_first30','beta_last30','beta_last36','beta_weekly_same_period','peer_median_raw_equity_beta','wacc','break_even_wacc','break_even_market_beta']].round(4).to_string(index=False))
print(pd.DataFrame(sensitivities).pivot(index='ticker', columns='scenario', values='cash_value').round(2).to_string())
