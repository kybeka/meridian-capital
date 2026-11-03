import importlib.util
from pathlib import Path
import unittest

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
