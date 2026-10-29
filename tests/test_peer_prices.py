import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_peer_prices import build_comparison


class PeerAccountingTests(unittest.TestCase):
    def setUp(self):
        self.team = dict(id='a', name='A', source_url='https://example.com', holdings_verified_on='2026-10-29', reference_date='2026-10-16', capital_usd=1000, cash_usd=0.08, positions={'ETF':dict(shares=10, price=100)})
        self.history = {'ETF':dict(closes={'2026-10-16':100,'2026-10-19':99}, dividends={'2026-10-19':1}, splits=[])}

    def test_dividend_and_rounded_cash_preserve_total_return(self):
        result = build_comparison([self.team],self.history)
        self.assertEqual(result['series'][0]['values'],[100,100])
        self.assertEqual(result['series'][0]['opening_reconciliation_usd'],.08)

    def test_opening_price_mismatch_is_rejected(self):
        self.history['ETF']['closes']['2026-10-16']=90
        with self.assertRaises(ValueError): build_comparison([self.team],self.history)

    def test_different_team_dates_are_rejected(self):
        other=copy.deepcopy(self.team);other['positions']={'OTHER':dict(shares=10,price=100)}
        self.history['OTHER']=dict(closes={'2026-10-16':100},dividends={},splits=[])
        with self.assertRaises(ValueError): build_comparison([self.team,other],self.history)

    def test_published_opening_capital_is_checked(self):
        self.team['cash_usd']=100
        with self.assertRaises(ValueError): build_comparison([self.team],self.history)

    def test_split_requires_review(self):
        self.history['ETF']['splits']=[{'numerator':2}]
        with self.assertRaises(ValueError): build_comparison([self.team],self.history)

    def test_all_preview_series_share_dates_and_start_at_100(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/'dist/data/peer-valuations.json').read_text())
        self.assertEqual(len(data['series']),5)
        for s in data['series']:
            self.assertEqual(s['values'][0],100)
            self.assertEqual(len(s['values']),len(data['dates']))
