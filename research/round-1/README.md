# Round 1: canonical Bloomberg analysis

This folder is the current source of truth. Bloomberg is the active dataset; earlier Yahoo inputs and the superseded Desktop pack are archived references.

## Run
From this folder, using an existing environment with NumPy, pandas, SciPy, openpyxl and matplotlib:

    python run_analysis.py
    python run_analysis.py --sensitivity

On Kyla's laptop prefix the command with conda run -n base.

The pipeline imports the original Bloomberg export, jointly reoptimizes seven eligible ETFs using 200 starts, checks feasible rounding, reruns the fixed-weight comparisons and historical-fit diagnostics, and independently verifies accounting and the risk-free conversion. The optional flag also reruns the separate 108-case sensitivity study. No script edits Excel or the report. Stress testing is not implemented yet.

## File map
- Data/Raw sources/AMC Bloomerg Data.xlsx: original export, unchanged.
- Data/month_end_prices.csv and monthly_returns.csv: active Bloomberg-derived inputs.
- Data/Archive Yahoo 2026-10-14/: earlier public-data inputs, not used by the active optimizer.
- Code/revalidate_bloomberg.py: import, optimizer, rounding checks and main comparison.
- Code/optimize_current.py: compatibility entry point to that same optimizer.
- Code/backtest.py and verify_backtest.py: historical diagnostics and independent verification.
- Results/recommended_weights.json: current optimized targets.
- Results/main_results.json, backtest_summary.csv and checkpoint_2.csv: current comparisons.
- positions.json: final whole-share quantities using supplied 16 October closing prices, USD 12.12 cash.
- Studies/constraint-sensitivity/: separate study; does not change the main allocation.
- Archive/Team Pack 2026-10-14/: complete superseded Desktop pack.
- Reference/Results/: earlier Yahoo results used for reconciliation only.

## Current method
Targets: SPY 26.08%, EEMV 9.66%, DBC 26.95%, SCHD 3.28%, VGSH 5.00%, STIP 29.03%. VWO remains eligible at zero; XLE is excluded.

Fit: 60 monthly returns, October 2021–September 2026. Fully invested, long only, 8% estimated volatility, 35% individual capital cap, 40% individual risk cap, 65% equity-risk cap, 5% building-block floors and 20% combined bond floor. Policy thresholds are chosen assumptions. Multiple solver starts do not prove global optimality.

The main backtest is retrospective, November 2016–September 2026. Fixed targets are restored monthly with 10 bp per dollar traded including inception. It is not an untouched holdout. FRED DGS1MO supplies the separate risk-free proxy. The same-six-ETF risk-parity benchmark is below the volatility band.

SPY's Bloomberg formula confirms dividend and split adjustments. Other ETF columns contain saved values without original adjustment flags. The first source date's formula error is corrected only in import code to 31 October 2011, as explicitly confirmed by Kyla. Bloomberg source data is included in this public repository at the user's express request.

## One working version
Use GitHub and the Desktop checkout for all future code changes. ZIPs are commit exports, never editable primary copies. Commit source changes, inputs and regenerated results together. The website is a separate presentation and is not automatically rebuilt by this pipeline; its last published allocation may differ until separately updated.
