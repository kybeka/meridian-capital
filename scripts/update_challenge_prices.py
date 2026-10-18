"""Value confirmed holdings from Yahoo daily closes; never replace the opening NAV."""
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
            nav += holding['shares'] * (history['closes'][day] + distributions)
        rows.append((day, f'{nav:.2f}', 'Yahoo daily close plus cash and dividend receivables'))
    return rows


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
    positions = json.loads((ROOT / 'research/tracking/opening-positions.json').read_text())
    now = datetime.now(NY)
    histories = {ticker: fetch_history(ticker, positions['reference_date'], now) for ticker in positions['positions']}
    rows = calculate(positions, histories)
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
    temporary = output.with_suffix('.tmp')
    temporary.write_text(buffer.getvalue())
    temporary.replace(output)
    print(f'Validated {len(rows)} valuations through {rows[-1][0]}')


if __name__ == '__main__':
    main()
