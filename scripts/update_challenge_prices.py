"""Value confirmed holdings from Yahoo daily closes; never replace the opening NAV."""
import argparse
import csv
import io
import json
import math
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
NY = ZoneInfo('America/New_York')


def apply_verified_distributions(ticker, history, ledger):
    """Fill missing vendor events once; reject a conflicting reported amount."""
    dividends = history['dividends'].copy()
    for event in ledger:
        if event['ticker'] != ticker:
            continue
        amount = event['amount']
        day = event['ex_date']
        if not math.isfinite(amount) or amount < 0:
            raise ValueError(f'{ticker}: invalid verified distribution on {day}')
        if day in dividends and not math.isclose(dividends[day], amount, rel_tol=0, abs_tol=1e-8):
            raise ValueError(f'{ticker}: vendor and issuer distributions conflict on {day}')
        dividends[day] = amount
    return {**history, 'dividends': dividends}


def calculate(positions, histories):
    opening = positions['reference_date']
    dates = None
    for ticker, history in histories.items():
        if history['splits']:
            raise ValueError(f'{ticker}: split detected; reconcile shares and price basis before updating')
        available = set(history['closes'])
        if not available:
            raise ValueError(f'{ticker}: no completed daily closes returned')
        if dates is None:
            dates = available
        elif dates != available:
            raise ValueError('ETF trading dates do not match; refusing a partial valuation')
    initial = positions['cash_usd'] + sum(p['shares'] * p['price'] for p in positions['positions'].values())
    if abs(initial - positions['capital_usd']) > .01:
        raise ValueError('Opening holdings and cash do not reconcile')
    rows = [(opening, f'{initial:.2f}', 'User-confirmed Bloomberg holdings at closing prices')]
    for day in sorted(d for d in dates if d > opening):
        nav = positions['cash_usd']
        for ticker, holding in positions['positions'].items():
            history = histories[ticker]
            # Ex-date entitlements remain in NAV as receivables, without reinvestment.
            distributions = sum(amount for ex_date, amount in history['dividends'].items() if opening < ex_date <= day)
            nav += holding['shares'] * (round(history['closes'][day], 2) + distributions)
        rows.append((day, f'{nav:.2f}', 'USD closes rounded to cents plus cash and issuer-verified distributions'))
    return rows


def contributions(positions, histories, rows):
    """Attribute fixed-share Round 1 P&L, including ex-date receivables."""
    tickers = list(positions['positions'])
    if set(tickers) != {'SPY', 'EEMV', 'DBC', 'VGSH', 'SCHD', 'STIP'}:
        raise ValueError('Contribution export is restricted to the published Round 1 ETFs')
    opening = positions['reference_date']
    initial = positions['capital_usd']
    previous = {t: p['shares'] * p['price'] for t, p in positions['positions'].items()}
    original = previous.copy()
    previous_nav = initial
    output = []
    for day, nav, _ in rows:
        if day > '2026-11-06':
            break
        values = original.copy() if day == opening else {
            t: positions['positions'][t]['shares'] * (round(histories[t]['closes'][day], 2) + sum(
                amount for ex, amount in histories[t]['dividends'].items() if opening < ex <= day
            )) for t in tickers
        }
        total = positions['cash_usd'] + sum(values.values())
        if abs(total - float(nav)) > .011:
            raise ValueError('Contribution values do not reconcile to portfolio NAV')
        output.append({'date': day, 'nav_usd': float(nav),
            'since': {t: (values[t] - original[t]) / initial * 100 for t in tickers},
            'daily': {t: (values[t] - previous[t]) / previous_nav * 100 for t in tickers}})
        previous, previous_nav = values, total
    return {'tickers': tickers, 'reference_date': opening, 'rows': output}


def calculate_timeline(snapshots, histories, link_rounds=False):
    """Value each confirmed basket over its holding period and carry attributed P&L."""
    if not snapshots or any(b['reference_date'] <= a['reference_date'] for a, b in zip(snapshots, snapshots[1:])):
        raise ValueError('Holding snapshots must be in chronological order')
    initial = snapshots[0]['capital_usd']
    tickers = list(dict.fromkeys(t for snapshot in snapshots for t in snapshot['positions']))
    cumulative = {t: 0.0 for t in tickers}
    rows, attribution, boundaries = [], [], []
    for index, snapshot in enumerate(snapshots):
        start = snapshot['reference_date']
        end = snapshots[index + 1]['reference_date'] if index + 1 < len(snapshots) else None
        selected = {}
        for ticker, holding in snapshot['positions'].items():
            if any(not math.isfinite(holding[k]) or holding[k] <= 0 for k in ('shares', 'price')):
                raise ValueError(f'{ticker}: invalid holding')
            history = histories[ticker]
            close = history['closes'].get(start)
            if close is None or abs(round(close, 2) - holding['price']) > .011:
                raise ValueError(f'{ticker}: snapshot price differs from closing price')
            selected[ticker] = {**history, 'closes': {
                d: v for d, v in history['closes'].items() if d >= start and (end is None or d <= end)
            }}
        if not math.isfinite(snapshot['cash_usd']) or snapshot['cash_usd'] < 0:
            raise ValueError('Invalid snapshot cash')
        basket = snapshot['cash_usd'] + sum(p['shares'] * p['price'] for p in snapshot['positions'].values())
        if abs(basket - snapshot['capital_usd']) > (1 if link_rounds else .011):
            raise ValueError('Snapshot holdings and cash do not reconcile to published capital')
        phase_rows = calculate({**snapshot, 'capital_usd': basket}, selected)
        scale = 1.0
        if rows:
            if rows[-1][0] != start:
                raise ValueError('Missing rebalance close')
            prior_nav = float(rows[-1][1])
            if not link_rounds and abs(prior_nav - basket) > .011:
                raise ValueError('Rebalance would create an unexplained NAV jump')
            scale = prior_nav / basket if link_rounds else 1.0
            boundaries.append({'date': start, 'prior_nav_usd': prior_nav,
                'published_basket_usd': round(basket, 2), 'difference_usd': round(basket-prior_nav, 2)})
        previous_values = {t: h['shares'] * h['price'] for t, h in snapshot['positions'].items()}
        previous_nav = basket * scale
        for day, _, source in phase_rows:
            if day == start and index:
                continue
            values = {t: h['shares'] * (h['price'] if day == start else
                round(selected[t]['closes'][day], 2) + sum(v for ex, v in selected[t]['dividends'].items() if start < ex <= day))
                for t, h in snapshot['positions'].items()}
            nav = (snapshot['cash_usd'] + sum(values.values())) * scale
            pnl = {t: (values.get(t, 0)-previous_values.get(t, 0))*scale for t in tickers}
            for ticker in tickers:
                cumulative[ticker] += pnl[ticker]
            if abs(initial + sum(cumulative.values()) - nav) > .011:
                raise ValueError('Attributed P&L does not reconcile to NAV')
            rows.append((day, f'{nav:.2f}', source))
            attribution.append({'date': day, 'nav_usd': round(nav, 2),
                'since': {t: cumulative[t]/initial*100 for t in tickers},
                'daily': {t: pnl[t]/previous_nav*100 for t in tickers}})
            previous_values, previous_nav = values, nav
    return rows, {'reference_date': snapshots[0]['reference_date'], 'tickers': tickers,
        'rebalance_dates': [s['reference_date'] for s in snapshots[1:]], 'rows': attribution}, boundaries


def fetch_history(ticker, opening, now):
    start = int(datetime.fromisoformat(opening).replace(tzinfo=NY).timestamp())
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?period1={start}&period2={int(now.timestamp())}&interval=1d&events=div%2Csplits&includeAdjustedClose=false'
    error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.load(response)['chart']['result'][0]
            break
        except Exception as exc:
            error = exc
            if attempt == 2:
                raise RuntimeError(f'{ticker}: price download failed') from error
            time.sleep(2 ** attempt)
    if result['meta'].get('currency') != 'USD':
        raise ValueError(f'{ticker}: unexpected currency')
    closes = {}
    for stamp, price in zip(result.get('timestamp', []), result['indicators']['quote'][0]['close']):
        date = datetime.fromtimestamp(stamp, NY).date()
        # Wait until 18:00 New York time even on early-close sessions.
        if date > now.date() or (date == now.date() and now.hour < 18):
            continue
        if price is None or not math.isfinite(price) or price <= 0:
            raise ValueError(f'{ticker}: invalid close on {date}')
        closes[date.isoformat()] = price
    events = result.get('events', {})
    dividends = {datetime.fromtimestamp(v['date'], NY).date().isoformat(): v['amount'] for v in events.get('dividends', {}).values()}
    if any(not math.isfinite(v) or v < 0 for v in dividends.values()):
        raise ValueError(f'{ticker}: invalid dividend')
    splits = [v for v in events.get('splits', {}).values() if datetime.fromtimestamp(v['date'], NY).date().isoformat() > opening]
    return {'closes': closes, 'dividends': dividends, 'splits': splits}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--history-file', type=Path)
    args = parser.parse_args()
    positions = json.loads((ROOT / 'research/tracking/opening-positions.json').read_text())
    round2 = json.loads((ROOT / 'research/tracking/round2-positions.json').read_text())
    ledger = json.loads((ROOT / 'research/tracking/verified-distributions.json').read_text())
    now = datetime.now(NY)
    tickers = set(positions['positions']) | set(round2['positions'])
    saved = json.loads(args.history_file.read_text()) if args.history_file else None
    histories = {ticker: apply_verified_distributions(ticker,
        saved[ticker] if saved else fetch_history(ticker, positions['reference_date'], now), ledger
    ) for ticker in sorted(tickers)}
    rows, attribution, _ = calculate_timeline([positions, round2], histories)
    if (now.date() - datetime.fromisoformat(rows[-1][0]).date()).days > 4:
        raise ValueError('Latest complete valuation is stale; preserving published data')
    output = ROOT / 'dist/data/challenge-valuations.csv'
    old = list(csv.DictReader(io.StringIO(output.read_text())))
    if old and rows[-1][0] < old[-1]['date']:
        raise ValueError('Downloaded history ends before the published series')
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator='\n')
    writer.writerow(['date', 'nav_usd', 'source'])
    writer.writerows(rows)
    attribution_path = ROOT / 'dist/data/portfolio-contributions.json'
    attribution_temp = attribution_path.with_suffix('.tmp')
    attribution_temp.write_text(json.dumps(attribution, indent=2) + '\n')
    temporary = output.with_suffix('.tmp')
    temporary.write_text(buffer.getvalue())
    temporary.replace(output)
    attribution_temp.replace(attribution_path)
    print(f'Validated {len(rows)} valuations through {rows[-1][0]}')


if __name__ == '__main__':
    main()
