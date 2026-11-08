"""Reconcile the frozen Round 1 closing NAV across the Checkpoint 2 deliverables."""
import argparse
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
ROUND2 = ROOT / 'research/round-2'
TRACKING = ROOT / 'research/tracking'
CUTOFF = '2026-11-06'


def reconcile(write=False):
    spec = importlib.util.spec_from_file_location('prices', ROOT / 'scripts/update_challenge_prices.py')
    prices = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prices)
    opening = json.loads((TRACKING / 'opening-positions.json').read_text())
    ledger = json.loads((TRACKING / 'verified-distributions.json').read_text())
    research_ledger = json.loads((ROUND2 / 'data/dividend_overrides.json').read_text())
    assert {(e['ticker'], e['ex_date'], e['amount']) for e in ledger} == {
        (e['ticker'], e['ex_date'], e['amount']) for e in research_ledger
    }
    histories = {}
    market_value = Decimal('0')
    ny = ZoneInfo('America/New_York')
    for ticker, position in opening['positions'].items():
        raw = json.loads((ROUND2 / f'data/prices/{ticker}.json').read_text())['chart']['result'][0]
        closes = {datetime.fromtimestamp(stamp, ny).date().isoformat(): value
                  for stamp, value in zip(raw['timestamp'], raw['indicators']['quote'][0]['close'])
                  if opening['reference_date'] <= datetime.fromtimestamp(stamp, ny).date().isoformat() <= CUTOFF}
        history = {'closes': closes, 'dividends': {
            datetime.fromtimestamp(event['date'], ny).date().isoformat(): event['amount']
            for event in raw.get('events', {}).get('dividends', {}).values()
        }, 'splits': []}
        histories[ticker] = prices.apply_verified_distributions(ticker, history, ledger)
        market_value += position['shares'] * Decimal(str(round(closes[CUTOFF], 2)))
    rows = prices.calculate(opening, histories)
    assert rows[-1][0] == CUTOFF
    distributions = []
    for event in ledger:
        if opening['reference_date'] < event['ex_date'] <= CUTOFF:
            shares = opening['positions'][event['ticker']]['shares']
            amount = Decimal(str(event['amount'])) * shares
            distributions.append({**event, 'entitled_shares': shares, 'entitlement_usd': str(amount),
                                  'paid_by_cutoff': event['pay_date'] <= CUTOFF})
    income = sum((Decimal(e['entitlement_usd']) for e in distributions), Decimal('0'))
    nav = market_value + Decimal(str(opening['cash_usd'])) + income
    assert abs(Decimal(rows[-1][1]) - nav) <= Decimal('.005')
    destination = ROOT / 'dist/data/challenge-valuations.csv'
    if write:
        previous = list(csv.DictReader(destination.open()))
        if previous[-1]['date'] > CUTOFF:
            raise ValueError('Later website observations exist; reconcile the trading ledger before replacing them.')
        with destination.open('w') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(['date', 'nav_usd', 'source'])
            writer.writerows(rows)
        (ROOT / 'dist/data/round1-contributions.json').write_text(
            json.dumps(prices.contributions(opening, histories, rows), indent=2) + '\n')
    published = list(csv.DictReader(destination.open()))
    website = next(row for row in published if row['date'] == CUTOFF)
    assert website['nav_usd'] == f'{nav:.2f}'
    notebook_nav = list(csv.DictReader((ROUND2 / 'results/round1_nav.csv').open()))[-1]['NAV USD']
    assert abs(Decimal(notebook_nav) - nav) < Decimal('.00001')
    implementation = json.loads((ROUND2 / 'results/implementation.json').read_text())
    assert abs(Decimal(str(implementation['nav'])) - nav) < Decimal('.00001')
    model = ROUND2 / 'submission/Meridian_Final_Model.xlsx'
    workbook = openpyxl.load_workbook(model, data_only=True)
    for address in ['D4', 'D24']:
        assert abs(Decimal(str(workbook['Portfolio'][address].value)) - nav) < Decimal('.00001')
    assert abs(Decimal(str(workbook['Portfolio']['D26'].value)) - Decimal('116.04561')) < Decimal('.00001')
    report = ROUND2 / 'submission/Meridian_Final_Selection.pdf'
    text = subprocess.check_output(['pdftotext', str(report), '-'], text=True)
    assert f'{nav:,.2f}' in text and f'{nav / 3:,.2f}' in text and '116.05' in text
    notebook = ROUND2 / 'round2_analysis.ipynb'
    notebook_json = json.loads(notebook.read_text())
    assert all(cell['execution_count'] is not None for cell in notebook_json['cells'] if cell['cell_type'] == 'code')
    assert f'{nav:,.2f}' in notebook.read_text()
    contributions = json.loads((ROOT / 'dist/data/round1-contributions.json').read_text())['rows'][-1]
    assert contributions['nav_usd'] == float(website['nav_usd'])
    assert abs(sum(contributions['since'].values()) - (float(nav) / opening['capital_usd'] - 1) * 100) < 1e-9
    result = {
        'price_date': CUTOFF, 'verified_on': '2026-11-08',
        'basis': 'Submitted opening holdings at raw USD closes rounded to cents plus opening cash and issuer-confirmed entitled distributions; no reinvestment or extra fees.',
        'closing_security_market_value_usd': str(market_value), 'opening_cash_usd': str(opening['cash_usd']),
        'entitled_distributions_usd': str(income), 'nav_usd_unrounded': str(nav),
        'nav_usd': f'{nav:.2f}', 'one_third_stock_target_usd': f'{nav/3:.2f}',
        'return_since_inception': float(nav / Decimal(str(opening['capital_usd'])) - 1),
        'old_website_nav_usd': '97014152.14', 'old_website_difference_usd': str(nav - Decimal('97014152.14')),
        'distributions': distributions,
        'artifacts_match': ['website NAV and ETF contributions', 'executed notebook and CSV', 'Excel Portfolio!D4 and D24', 'final report NAV and budget'],
        'artifact_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in [destination, notebook, model, report]},
        'bloomberg_status': 'Public closing-price reconstruction; actual Bloomberg booked cash and tax treatment were not accessed.',
    }
    if write:
        (TRACKING / 'nav-reconciliation-2026-11-06.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Rebuild the website series through the frozen cutoff and save the reconciliation.')
    print(json.dumps(reconcile(parser.parse_args().write), indent=2))
