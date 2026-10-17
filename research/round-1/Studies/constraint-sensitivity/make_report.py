"""Present the separate sensitivity results without editing shared deliverables."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parent
d=pd.read_csv(P/'Results/scenarios.csv').set_index('scenario')
b=pd.read_csv(P/'Results/retrospective_context.csv').set_index('scenario')
assert len(d)==108 and d.feasible_solution_found.all()
assert d.seed_objective_gap.max()<1e-9
assert np.max(abs(d.estimated_volatility-.08))<1e-7
assert d[['verified_seed17','verified_seed83']].min().min()>0
assets=['SPY','EEMV','DBC','SCHD','VGSH','STIP']
selected=['risk_cap=0.350','risk_cap=0.375','Baseline','risk_cap=0.425','risk_cap=0.450']
labels=['35%','37.5%','40% (current)','42.5%','45%']
fig,ax=plt.subplots(figsize=(10,5.2))
colors=['#315b83','#8bb5cf','#cf954d','#8a7ba7','#98b7a1','#c9d9e6']
bottom=np.zeros(5)
for a,c in zip(assets,colors):
    vals=d.loc[selected,a].values*100
    ax.bar(labels,vals,bottom=bottom,label=a,color=c,width=.65)
    for j,y in enumerate(vals):
        if y>6:ax.text(j,bottom[j]+y/2,f'{y:.1f}%',ha='center',va='center',fontsize=9)
    bottom+=vals
ax.set_ylim(0,100);ax.set_ylabel('Capital allocation (%)');ax.set_xlabel('Maximum risk contribution per ETF')
ax.set_title('Risk cap changes the allocation',loc='left',pad=18)
ax.spines[['top','right']].set_visible(False)
ax.legend(ncol=6,loc='upper center',bbox_to_anchor=(.5,-.15),frameon=False)
fig.text(.125,.01,'Same Bloomberg inputs and 8% estimated volatility. VWO receives zero throughout.',fontsize=9)
fig.tight_layout(rect=(0,.05,1,1))
fig.savefig(P/'Results/risk_cap_allocations.png',dpi=180)
fig.savefig(P/'Results/risk_cap_allocations.pdf')
table=d.loc[selected,assets].mul(100).round(2)
table['Capital moved (%)']=d.loc[selected,'reallocated_capital_pct'].round(2)
table.index=labels
summary='''CONSTRAINT SENSITIVITY — SEPARATE STUDY

Nothing in the shared Excel workbook or Google Doc was changed by this study.

CONCLUSION
The 40% individual-ETF risk cap and VGSH capital minimum materially shape the current allocation. The other tested limits mostly act as safeguards rather than determining today's weights. Small risk-cap changes produce moderate shifts. Wider combined changes can produce substantial shifts and remove SCHD. The exact current weights are therefore conditional on our policy choices, not a uniquely robust optimum.

WHAT WAS TESTED
108 distinct specifications: one baseline, 17 one-limit changes, 10 individual building-block floor changes, and 80 joint changes.
Risk cap: 35%, 37.5%, 40%, 42.5%, 45%.
Common building-block floor: 2.5%, 5%, 7.5%.
Individual floors: US, emerging markets, commodities, VGSH and STIP, each separately at 2.5% and 7.5%.
Combined bond minimum: 15%, 20%, 25%, 30%.
Capital cap: 30%, 32.5%, 35%, 37.5%, 40%.
Combined equity-risk cap: 55%, 60%, 65%, 70%, 75%.
Joint grid: risk cap 35/40/45%; common floor 2.5/5/7.5%; capital cap 30/35/40%; equity-risk cap 60/65/70%; bond minimum held at 20%.

CONTROLLED METHODOLOGY
Same seven eligible ETFs, XLE excluded, Bloomberg monthly returns October 2021–September 2026, same historical-mean objective, long only, fully invested, and exact 8% estimated volatility throughout. All weights were reoptimized jointly. Forty-eight SLSQP starts per scenario, split between two seeds, include the existing optimum and an equal-weight start. All 108 scenarios produced verified feasible solutions; both seeds agreed on the best objective within 1e-9. Monthly-return-based risk calculations independently confirmed covariance-based risk contributions. Multiple starts are not proof of global optimality. The sensitivity comparisons use unrounded optimized weights to avoid rounding noise.

RESULTS
'''+table.to_string()+'''

Capital moved = half the sum of absolute weight changes from the full-precision baseline. It measures the fraction of portfolio capital that must be reassigned, not a change in volatility.

1. Risk cap: at 37.5% and 42.5%, respectively 3.64% and 3.83% of capital moves; the largest single weight changes by about 2.34 and 2.44 percentage points. Across 35–45%, the changes are larger: 7.10–11.76% of capital moves. SCHD falls to zero at 45%, so its presence is sensitive to this policy.
2. VGSH minimum: lowering it to 2.5% changes VGSH to 2.5% and STIP to 31.84%; increasing it to 7.5% changes VGSH to 7.5% and STIP to 26.22%. Roughly 2.82% of capital moves either way. Other building-block floors have effectively no effect when changed individually over this range.
3. Other safeguards: bond minimum 15–30%, ETF capital cap 30–40%, and equity-risk cap 55–75% leave the baseline weights effectively unchanged when varied individually. The baseline already has 34.03% bonds, a largest ETF weight of 29.03%, and equity risk of 53.40%.
4. Joint changes: the largest tested capital reassignment is 24.49%. For example, 45% individual risk cap and 7.5% floors (35% capital cap, 65% equity-risk cap) yield SPY 29.67%, EEMV 7.50%, DBC 29.49%, SCHD 0%, VGSH 23.36%, STIP 9.97%. This is a wider combined change, not a tiny adjustment of one parameter. VWO remains zero across all 108 specifications.

DOES THE HISTORICAL BACKTEST SUPPORT ONE LIMIT?
No. The same retrospective backtest is supplied for context only, not to choose thresholds. At the 35%, 40%, and 45% individual risk caps, respective retrospective Sharpes are approximately 0.758, 0.768 and 0.782. These small differences do not establish which limit will perform best in future. The inputs and evaluation history have already been inspected.

RECOMMENDATION
Keep the current 40% cap if the team accepts the compromise: more concentration than a 35% cap, but less than a 45% cap that drops SCHD. This study does not establish that 40% is optimal. Treat the 5% nominal-Treasury minimum as an intentional exposure choice: the optimizer consistently sits on that floor. Keep the other limits as safeguards without claiming that they caused the current allocation. Do not adjust limits merely to improve retrospective Sharpe.

POSSIBLE REPORT WORDING (NOT INSERTED INTO THE SHARED REPORT)
We tested the sensitivity of the allocation to 108 constraint specifications using unchanged Bloomberg inputs and an 8% estimated volatility target. The individual-ETF risk cap and minimum nominal-Treasury allocation were the main binding policy choices. Changing the risk cap from 40% to 37.5% or 42.5% required reallocating approximately 3.6–3.8% of capital. Nearby changes to the combined bond minimum, capital cap and equity-risk cap had no material effect individually. Wider joint changes produced larger shifts, so our exact weights remain conditional on the selected policy limits. The thresholds are portfolio-design choices rather than statistically optimal values.

FILES
run_sensitivity.py — reproducible optimization, feasibility checks, and retrospective context.
make_report.py — this summary and the allocation chart.
Data/ — copies of the source returns and FRED proxy; source files remain unchanged.
Results/scenarios.csv — all 108 scenarios, weights, risks, feasibility and seed agreement.
Results/one_limit_results.csv — baseline and individual constraint changes.
Results/retrospective_context.csv — historical diagnostics; not used for policy selection.
Results/risk_cap_allocations.png and .pdf — comparison chart.
Results/verification.json — methodology and source hashes.
'''
(P/'START HERE.txt').write_text(summary)
print(summary)
