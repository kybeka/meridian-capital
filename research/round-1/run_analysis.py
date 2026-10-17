"""Run the canonical Bloomberg analysis and independent backtest verification."""
from pathlib import Path
import subprocess
import sys
import argparse
import json
import pandas as pd

P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--sensitivity',action='store_true',help='Also rerun the separate 108-case sensitivity study')
args=parser.parse_args()
for name in ['revalidate_bloomberg.py','backtest.py','verify_backtest.py']:
    subprocess.run([sys.executable,str(P/'Code'/name)],check=True)
record=json.loads((P/'Results/recommended_weights.json').read_text())
pd.DataFrame({'weight':record['rounded_weights'],'risk_share':record['rounded_risk_shares']}).to_csv(P/'Results/allocation.csv')
if args.sensitivity:
    for name in ['run_sensitivity.py','make_report.py']:
        subprocess.run([sys.executable,str(P/'Studies/constraint-sensitivity'/name)],check=True)
print('Canonical Bloomberg analysis and verification completed.')
