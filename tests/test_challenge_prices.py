import importlib.util
import json
from datetime import datetime
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo

spec = importlib.util.spec_from_file_location('prices', Path(__file__).resolve().parents[1] / 'scripts/update_challenge_prices.py')
prices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prices)


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.positions = {'reference_date': '2026-10-16', 'cash_usd': 10, 'capital_usd': 1010, 'positions': {'ETF': {'shares': 10, 'price': 100}}}
        self.history = {'ETF': {'closes': {'2026-10-16': 99, '2026-10-19': 101, '2026-10-20': 100}, 'dividends': {'2026-10-16': 5, '2026-10-20': 1}, 'splits': []}}

    def test_opening_anchor_and_dividend_no_reinvestment(self):
        rows = prices.calculate(self.positions, self.history)
        self.assertEqual([r[1] for r in rows], ['1010.00', '1020.00', '1020.00'])
        self.assertEqual(rows, prices.calculate(self.positions, self.history))

    def test_split_requires_reconciliation(self):
        self.history['ETF']['splits'] = [{'numerator': 2, 'denominator': 1}]
        with self.assertRaises(ValueError):
            prices.calculate(self.positions, self.history)

    def test_issuer_event_is_credited_on_ex_date_once(self):
        ledger = [{'ticker': 'ETF', 'ex_date': '2026-10-20', 'pay_date': '2026-10-22', 'amount': 1}]
        missing = {**self.history['ETF'], 'dividends': {}}
        corrected = prices.apply_verified_distributions('ETF', missing, ledger)
        repeated = prices.apply_verified_distributions('ETF', corrected, ledger)
        self.assertEqual(corrected, repeated)
        self.assertEqual(missing['dividends'], {})
        self.assertEqual([r[1] for r in prices.calculate(self.positions, {'ETF': repeated})],
                         ['1010.00', '1020.00', '1020.00'])

    def test_conflicting_vendor_event_is_rejected(self):
        ledger = [{'ticker': 'ETF', 'ex_date': '2026-10-20', 'amount': 2}]
        with self.assertRaisesRegex(ValueError, 'conflict'):
            prices.apply_verified_distributions('ETF', self.history['ETF'], ledger)

    def test_vendor_rounding_preserves_documented_dividend_precision(self):
        for ticker, exact, rounded in [('STIP', .292917, .293), ('VGSH', .1889, .189),
                                       ('BIL', .30849, .308), ('TIP', .161241, .161)]:
            with self.subTest(ticker=ticker):
                history = {'closes': {}, 'dividends': {'2026-11-02': rounded}, 'splits': []}
                ledger = [{'ticker': ticker, 'ex_date': '2026-11-02', 'amount': exact}]
                corrected = prices.apply_verified_distributions(ticker, history, ledger)
                self.assertEqual(corrected['dividends']['2026-11-02'], exact)
                self.assertEqual(prices.apply_verified_distributions(ticker, corrected, ledger), corrected)
                self.assertEqual(history['dividends']['2026-11-02'], rounded)

    def test_small_non_rounding_discrepancy_is_still_rejected(self):
        ledger = [{'ticker': 'STIP', 'ex_date': '2026-11-02', 'amount': .292917}]
        for vendor in [.2928, .294, 0, float('nan')]:
            with self.subTest(vendor=vendor), self.assertRaisesRegex(ValueError, 'conflict'):
                prices.apply_verified_distributions('STIP', {'dividends': {'2026-11-02': vendor}}, ledger)

    def test_close_precision_matches_notebook(self):
        self.history['ETF']['closes']['2026-10-19'] = 100.999998
        self.assertEqual(prices.calculate(self.positions, self.history)[1][1], '1020.00')

    def test_missing_price_does_not_make_partial_portfolio(self):
        self.positions['positions']['OTHER'] = {'shares': 0, 'price': 100}
        self.history['OTHER'] = {'closes': {'2026-10-16': 100}, 'dividends': {}, 'splits': []}
        with self.assertRaises(ValueError):
            prices.calculate(self.positions, self.history)


class ContributionTests(unittest.TestCase):
    def test_dividends_and_daily_denominator(self):
        tickers = ['SPY','EEMV','DBC','VGSH','SCHD','STIP']
        positions = {'reference_date':'2026-10-16','cash_usd':10,'capital_usd':610,
                     'positions':{t:{'shares':1,'price':100} for t in tickers}}
        histories = {t:{'closes':{'2026-10-16':100,'2026-10-19':110,'2026-10-20':108,'2026-10-21':109},
                        'dividends':{'2026-10-20':2},'splits':[]} for t in tickers}
        rows = prices.calculate(positions,histories)
        result = prices.contributions(positions,histories,rows)['rows']
        self.assertEqual(sum(result[0]['since'].values()),0)
        self.assertAlmostEqual(sum(result[1]['since'].values()),60/610*100)
        self.assertEqual(sum(result[2]['daily'].values()),0)
        self.assertAlmostEqual(sum(result[3]['daily'].values()),6/670*100)
        for i, row in enumerate(result):
            self.assertAlmostEqual(sum(row['since'].values()),(row['nav_usd']/610-1)*100)
            previous=result[max(0,i-1)]['nav_usd']
            self.assertAlmostEqual(sum(row['daily'].values()),(row['nav_usd']/previous-1)*100)

    def test_private_or_unexpected_holdings_are_rejected(self):
        with self.assertRaises(ValueError):
            prices.contributions({'positions':{'OTHER':{}}},{},[])


class FrozenNovemberBookTests(unittest.TestCase):
    def test_missing_vendor_distributions_reconcile_to_checkpoint_nav(self):
        root = Path(__file__).resolve().parents[1]
        positions = json.loads((root / 'research/tracking/opening-positions.json').read_text())
        ledger = json.loads((root / 'research/tracking/verified-distributions.json').read_text())
        histories = {}
        for ticker in positions['positions']:
            raw = json.loads((root / f'research/round-2/data/prices/{ticker}.json').read_text())['chart']['result'][0]
            closes = {datetime.fromtimestamp(stamp, ZoneInfo('America/New_York')).date().isoformat(): close
                      for stamp, close in zip(raw['timestamp'], raw['indicators']['quote'][0]['close'])
                      if datetime.fromtimestamp(stamp, ZoneInfo('America/New_York')).date().isoformat()
                      in ['2026-10-16', '2026-11-02', '2026-11-06']}
            histories[ticker] = prices.apply_verified_distributions(
                ticker, {'closes': closes, 'dividends': {}, 'splits': []}, ledger)
        rows = prices.calculate(positions, histories)
        self.assertEqual(rows[-1][1], '97115068.58')
        contributions = prices.contributions(positions, histories, rows)
        self.assertEqual(contributions['rows'][-1]['nav_usd'], 97115068.58)


class RebalanceTests(unittest.TestCase):
    def setUp(self):
        self.opening = dict(reference_date='2026-10-16', capital_usd=1000, cash_usd=0,
                            positions={'ETF': dict(shares=10, price=100)})
        self.rebalance = dict(reference_date='2026-11-06', capital_usd=1110, cash_usd=10,
                              positions={'ETF': dict(shares=5, price=110), 'STOCK': dict(shares=11, price=50)})
        self.histories = {
            'ETF': dict(closes={'2026-10-16':100,'2026-11-06':110,'2026-11-09':111},
                        dividends={'2026-11-06':1,'2026-11-09':2}, splits=[]),
            'STOCK': dict(closes={'2026-11-06':50,'2026-11-09':51},dividends={},splits=[])}

    def test_rebalance_preserves_history_and_uses_entitled_quantities(self):
        rows, attribution, boundaries = prices.calculate_timeline([self.opening,self.rebalance],self.histories)
        self.assertEqual([r[1] for r in rows],['1000.00','1110.00','1136.00'])
        self.assertEqual(boundaries[0]['difference_usd'],0)
        final=attribution['rows'][-1]
        self.assertAlmostEqual(final['since']['ETF'],12.5)
        self.assertAlmostEqual(final['since']['STOCK'],1.1)
        self.assertAlmostEqual(sum(final['daily'].values()),26/1110*100)
        self.assertEqual(attribution['rows'][1]['since']['STOCK'],0)

    def test_unexplained_own_rebalance_jump_fails(self):
        self.rebalance['cash_usd']+=100
        self.rebalance['capital_usd']+=100
        with self.assertRaisesRegex(ValueError,'NAV jump'):
            prices.calculate_timeline([self.opening,self.rebalance],self.histories)

    def test_peer_round_returns_link_without_artificial_gain(self):
        self.rebalance['cash_usd']+=100
        self.rebalance['capital_usd']+=100
        rows, _, boundaries=prices.calculate_timeline([self.opening,self.rebalance],self.histories,link_rounds=True)
        self.assertAlmostEqual(float(rows[-1][1]),1110*(1236/1210),places=2)
        self.assertEqual(boundaries[0]['difference_usd'],100)

    def test_missing_rebalance_close_fails(self):
        del self.histories['STOCK']['closes']['2026-11-06']
        with self.assertRaisesRegex(ValueError,'snapshot price'):
            prices.calculate_timeline([self.opening,self.rebalance],self.histories)

    def test_published_contributions_and_peer_line_match_nav(self):
        import csv
        root=Path(__file__).resolve().parents[1]
        rows=list(csv.DictReader((root/'dist/data/challenge-valuations.csv').read_text().splitlines()))
        attribution=json.loads((root/'dist/data/portfolio-contributions.json').read_text())['rows']
        peers=json.loads((root/'dist/data/peer-valuations.json').read_text())
        own=next(s for s in peers['series'] if s['id']=='meridian')
        peer_values=dict(zip(peers['dates'],own['values']))
        self.assertEqual(len(rows),len(attribution))
        for i,(row,entry) in enumerate(zip(rows,attribution)):
            nav=float(row['nav_usd']); previous=float(rows[max(0,i-1)]['nav_usd'])
            self.assertEqual(entry['date'],row['date'])
            self.assertAlmostEqual(sum(entry['since'].values()),(nav/1e8-1)*100,places=7)
            self.assertAlmostEqual(sum(entry['daily'].values()),(nav/previous-1)*100,places=7)
            if row['date'] in peer_values:
                self.assertAlmostEqual(peer_values[row['date']],nav/1e6,places=7)
