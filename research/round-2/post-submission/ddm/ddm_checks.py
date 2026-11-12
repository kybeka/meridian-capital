"""Reproduce the 10 November dividend checks using the saved 6 November inputs."""

from pathlib import Path
import csv
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1]
INPUT_PATH = SOURCE / 'results/valuation/inputs.json'
STOCKS = ['KR', 'HRL', 'BMY', 'XOM', 'HPQ']
inputs = {row['ticker']: row for row in json.loads(INPUT_PATH.read_text())}


def gordon(dividend_rate, equity_rate, growth):
    if dividend_rate <= 0 or equity_rate <= growth:
        raise ValueError('Require a positive dividend and an equity discount rate above perpetual growth.')
    return dividend_rate * (1 + growth) / (equity_rate - growth)


def two_stage(dividend_rate, equity_rate, initial_growth, terminal_growth, years=5):
    if years < 1 or equity_rate <= terminal_growth:
        raise ValueError('Require a positive forecast period and an equity rate above terminal growth.')
    forecast = [dividend_rate * (1 + initial_growth) ** year for year in range(1, years + 1)]
    terminal = forecast[-1] * (1 + terminal_growth) / (equity_rate - terminal_growth)
    discounted_dividends = sum(dividend / (1 + equity_rate) ** year for year, dividend in enumerate(forecast, 1))
    discounted_terminal = terminal / (1 + equity_rate) ** years
    return discounted_dividends + discounted_terminal


def implied_perpetual_growth(dividend_rate, equity_rate, price):
    return (price * equity_rate - dividend_rate) / (price + dividend_rate)


scenarios, summary = [], []
for ticker in STOCKS:
    row = inputs[ticker]
    d, k = row['dividend'], row['k']
    target, entry = row['multiple_value'], row['price']
    saved_growth = row['dividend_growth']
    for growth in [0, .01, .02, .03]:
        value = gordon(d, k, growth)
        scenarios.append(dict(ticker=ticker, scenario=f'Constant dividend growth {growth:.0%}',
                              current_annualized_dividend=d, cost_equity=k, initial_growth=growth, terminal_growth=growth,
                              dividend_scale=1, value=value, entry_price=entry, submitted_value=target,
                              upside_to_entry=value / entry - 1, difference_to_submitted=value / target - 1))
        assert math.isclose(value, two_stage(d, k, growth, growth), rel_tol=1e-12)
    other_scenarios = [
        ('Saved dividend-growth assumption', d, k, saved_growth, saved_growth),
        ('Flat dividends for 5 years, then 2%', d, k, 0, .02),
        ('25% initial dividend cut, then 2% growth', .75 * d, k, .02, .02),
        ('2% dividend growth, equity rate +1pp', d, k + .01, .02, .02),
        ('2% dividend growth, equity rate +2pp', d, k + .02, .02, .02),
    ]
    for label, dividend, rate, first, terminal in other_scenarios:
        value = two_stage(dividend, rate, first, terminal)
        scenarios.append(dict(ticker=ticker, scenario=label, current_annualized_dividend=d,
                              cost_equity=rate, initial_growth=first, terminal_growth=terminal,
                              dividend_scale=dividend / d, value=value, entry_price=entry, submitted_value=target,
                              upside_to_entry=value / entry - 1, difference_to_submitted=value / target - 1))
    entry_growth = implied_perpetual_growth(d, k, entry)
    target_growth = implied_perpetual_growth(d, k, target)
    assert math.isclose(gordon(d, k, entry_growth), entry, rel_tol=1e-12)
    assert math.isclose(gordon(d, k, target_growth), target, rel_tol=1e-12)
    assert gordon(d, k + .01, .02) < gordon(d, k, .02)
    summary.append(dict(ticker=ticker, entry_price=entry, submitted_value=target,
                        current_annualized_dividend=d, cost_equity=k,
                        saved_dividend_growth=saved_growth, value_saved_growth=gordon(d, k, saved_growth),
                        value_uniform_2pct_growth=gordon(d, k, .02),
                        value_flat_5years_then_2pct=two_stage(d, k, 0, .02),
                        value_2pct_growth_equity_rate_plus1pp=gordon(d, k + .01, .02),
                        entry_implied_perpetual_growth=entry_growth,
                        target_implied_perpetual_growth=target_growth,
                        target_break_even_equity_rate_at_2pct=.02 + d * 1.02 / target,
                        entry_break_even_equity_rate_at_2pct=.02 + d * 1.02 / entry,
                        earnings_dividend_payout_proxy=d / row['eps']))


def save_csv(name, rows):
    with (HERE / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


save_csv('ddm_summary.csv', summary)
save_csv('ddm_scenarios.csv', scenarios)
metadata = {
    'audit_date': '2026-11-10', 'valuation_reference_date': '2026-11-06',
    'source': INPUT_PATH.relative_to(SOURCE).as_posix(),
    'source_sha256': hashlib.sha256(INPUT_PATH.read_bytes()).hexdigest(),
    'conventions': [
        'Use saved current annualized dividend rates as D0, with next annual dividend D1=D0*(1+g). This is an annual timing approximation.',
        'The saved dividend rates are not newly verified live declarations or guaranteed next-year payments.',
        'Use the submitted equity discount rate k, not WACC. Its beta uncertainty remains present in every DDM result.',
        'Uniform 2% perpetual dividend growth is an illustrative common scenario, not an independently estimated forecast.',
        'The saved growth assumption was 2% for KR, HRL, XOM and HPQ, and 0% for BMY. These were cash-retention scenario inputs, not a standalone submitted DDM.',
        'No buyback amount, cash balance or retained earnings is added separately. Their effect on future per-share dividends would require an explicit payout/share-count model.',
        'Implied growth solves for the assumption needed to match entry or target; it is not evidence that such growth is achievable.',
        'The original report, workbook, notebooks and holdings remain unchanged.',
    ],
    'checks': {'constant_growth_equals_two_stage_when_growth_matches': True,
               'all_implied_growth_roots_reprice_entry_and_target': True,
               'higher_equity_discount_rates_reduce_values': True},
}
(HERE / 'methodology.json').write_text(json.dumps(metadata, indent=2) + '\n')
for row in summary:
    print(row['ticker'], 'entry', row['entry_price'], 'target', row['submitted_value'],
          'k', round(100 * row['cost_equity'], 2), 'saved-growth value', round(row['value_saved_growth'], 2),
          '2% growth value', round(row['value_uniform_2pct_growth'], 2),
          '+1pp k value', round(row['value_2pct_growth_equity_rate_plus1pp'], 2),
          'growth for entry/target %', round(100 * row['entry_implied_perpetual_growth'], 2),
          round(100 * row['target_implied_perpetual_growth'], 2))
