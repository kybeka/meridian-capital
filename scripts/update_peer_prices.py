"""Reconstruct published Round 1 baskets on one daily-price and dividend basis."""
import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from update_challenge_prices import ROOT, NY, calculate, fetch_history


def build_comparison(teams, histories):
    dates = None
    series = []
    for team in teams:
        if team['reference_date'] != '2026-10-16':
            raise ValueError('All portfolios must share the opening date')
        selected = {ticker: histories[ticker] for ticker in team['positions']}
        initial = team['cash_usd']
        for ticker, p in team['positions'].items():
            if not math.isfinite(p['shares']) or p['shares'] <= 0 or not math.isfinite(p['price']) or p['price'] <= 0:
                raise ValueError('Invalid opening holding')
            initial += p['shares'] * p['price']
            opening = selected[ticker]['closes'].get(team['reference_date'])
            if opening is None or abs(opening - p['price']) > .011:
                raise ValueError(f'{ticker}: opening price basis differs from published holdings')
        # Some sites publish residual cash rounded to whole dollars. Preserve it.
        if abs(initial - team['capital_usd']) > 1:
            raise ValueError(f"{team['name']}: opening capital fails reconciliation")
        rows = calculate({**team, 'capital_usd': initial}, selected)
        current_dates = [row[0] for row in rows]
        if dates is not None and current_dates != dates:
            raise ValueError('Teams have different valuation dates')
        dates = current_dates
        series.append({key: team[key] for key in ('id', 'name', 'source_url', 'holdings_verified_on')} | {
            'opening_reconciliation_usd': round(initial - team['capital_usd'], 2),
            'values': [round(float(row[1]) / initial * 100, 8) for row in rows],
        })
    return {'dates': dates, 'series': series, 'basis': 'Published Round 1 shares held unchanged; daily USD closes, cash and ex-date dividend receivables.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--history-file', type=Path, help='Use saved public-price responses for reproducible checks')
    args = parser.parse_args()
    own = json.loads((ROOT / 'research/tracking/opening-positions.json').read_text())
    own.update(id='meridian', name='Meridian Capital', source_url='https://github.com/kybeka/meridian-capital/blob/main/research/tracking/opening-positions.json', holdings_verified_on='2026-10-16')
    teams = [own] + json.loads((ROOT / 'research/tracking/peer-positions.json').read_text())
    now = datetime.now(NY)
    tickers = sorted({t for team in teams for t in team['positions']})
    histories = json.loads(args.history_file.read_text()) if args.history_file else {t: fetch_history(t, own['reference_date'], now) for t in tickers}
    # Freeze at the Round 1 close until subsequent trades have been reviewed.
    cutoff = '2026-11-06'
    for history in histories.values():
        history['closes'] = {d: v for d, v in history['closes'].items() if d <= cutoff}
        history['splits'] = [event for event in history['splits'] if datetime.fromtimestamp(event['date'], NY).date().isoformat() <= cutoff]
    data = build_comparison(teams, histories)
    if data['dates'][-1] < cutoff and (now.date() - datetime.fromisoformat(data['dates'][-1]).date()).days > 4:
        raise ValueError('Stale prices; preserving comparison')
    output = ROOT / 'dist/data/peer-valuations.json'
    if output.exists() and json.loads(output.read_text())['dates'][-1] > data['dates'][-1]:
        raise ValueError('History ends before published comparison')
    temp = output.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(output)
    print(f"Validated {len(teams)} portfolios through {data['dates'][-1]}")


if __name__ == '__main__':
    main()
