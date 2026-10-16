# Round 1 — allocation code and data

This folder reproduces Meridian Capital’s proposed Strategic Asset Allocation (SAA) and the historical comparisons used in its Round 1 report. It uses the corrected **fixed-weight, monthly-rebalanced backtest** from the AMC Team Pack dated 14 October 2026. The Python scripts and reference data are copied unchanged from that pack.

This is an academic simulation. The results below are historical calculations, not live challenge performance. Official share quantities and execution prices are not part of this research snapshot.

## Start here

- **Understand the allocation:** read the method below and [Results/allocation.csv](Results/allocation.csv).
- **Check the report figures:** open [Results/backtest_summary.csv](Results/backtest_summary.csv) and [Results/checkpoint_2.csv](Results/checkpoint_2.csv).
- **Find the data sources:** read [Data/README.md](Data/README.md) and [Data/sources.json](Data/sources.json).
- **Reproduce the calculations:** run the three scripts in the order below. They work offline with the included files.

## Run the analysis

Download or clone this repository, keeping this folder’s structure intact. Use an existing Python environment with NumPy, pandas and SciPy. The calculation snapshot was checked with Python 3.13.5 and the versions recorded in [requirements.txt](requirements.txt). If your environment needs these dependencies, install them in that environment with `python -m pip install -r requirements.txt`.

From this folder:

```sh
python Code/optimize_current.py
python Code/backtest.py
python Code/verify_backtest.py
```

For an existing Conda environment, the equivalent is `conda run -n YOUR_ENV python Code/optimize_current.py`, and likewise for the other scripts.

| File | What it does |
| --- | --- |
| [Code/optimize_current.py](Code/optimize_current.py) | Estimates the inputs, optimizes all seven eligible weights jointly, and checks that the rounded recommendation matches the saved allocation. |
| [Code/backtest.py](Code/backtest.py) | Simulates the fixed MVO, equal-weight and risk-parity portfolios, including trading costs. It also runs two separate historical-fit checks and a bootstrap uncertainty calculation. |
| [Code/verify_backtest.py](Code/verify_backtest.py) | Rebuilds returns from month-end prices, verifies the Treasury-yield conversion, and independently reconciles the saved backtests using dollar holdings and trading costs. |

Reruns overwrite calculated JSON and monthly-return files in `Results`. The summary and allocation CSVs are frozen reference tables; these scripts do not regenerate every CSV. The optimizer deliberately fails if changed data produces a different rounded recommendation, and the verification script checks the saved protocols. If adapting the model, work in a copy, update the assumptions and reference outputs together, and do not treat the frozen tables as refreshed results.

## Allocation and method

| ETF | Capital weight |
| --- | ---: |
| SPY | 26.08% |
| EEMV | 9.63% |
| DBC | 26.95% |
| SCHD | 3.29% |
| VGSH | 5.00% |
| STIP | 29.05% |
| **Total** | **100.00%** |

VWO remains eligible but receives zero weight. XLE is excluded. Both remain in the source dataset so the original input files are preserved.

1. Convert adjusted USD month-end prices into simple monthly returns: `price / previous_price - 1`.
2. Use the latest 60 complete returns, **October 2021–September 2026**. Annual mean input is the monthly arithmetic mean × 12; annual covariance is monthly sample covariance × 12.
3. Maximize estimated annual return, `weights · mean_returns`, with all weights chosen jointly. Portfolio volatility is `sqrt(weightsᵀ · covariance · weights)`.
4. Require weights to sum to 100%, no short positions or leverage, and **8% estimated annual volatility**, within the challenge’s 7–9% band.
5. Apply the additional policy constraints below. These limits are chosen inputs, not weights discovered by the optimizer.
6. Use SciPy SLSQP with analytic derivatives and 200 starting points across two seeds. Repeated solutions support numerical stability; they do not prove a global optimum. Round only after optimization and recheck risk.

The rounded allocation has **7.9990% estimated annual volatility**. Python generated the weights; the report’s Excel model contains corresponding calculations.

### Additional policy constraints

- Maximum 35% of capital in any eligible ETF.
- Minimum 5% combined in SPY + SCHD, and 5% combined in VWO + EEMV.
- Minimum 5% each in DBC, VGSH and STIP.
- Minimum 20% combined in VGSH + STIP.
- Maximum 40% of total risk from any ETF, and 65% combined from equities.

Risk share is `weight_i × (covariance · weights)_i / portfolio_variance`. It differs from capital weight. SPY and DBC each contribute approximately 40% of estimated risk, so this portfolio is **constrained MVO, not risk parity**.

## Main backtest

The proposed target weights stay fixed throughout **November 2016–September 2026**, a common period of 119 monthly returns. Monthly rebalancing restores the targets after market movements; it does not re-optimize them quarterly. Equal weight and risk parity use the same six selected ETFs and evaluation period. Their target weights are also fixed.

| Fixed allocation | Annual return (CAGR) | Realized volatility | Sharpe | Maximum month-end drawdown |
| --- | ---: | ---: | ---: | ---: |
| Proposed MVO | 9.04% | 8.60% | 0.768 | −16.19% |
| Equal weight | 8.49% | 8.30% | 0.731 | −15.17% |
| Risk parity | 4.46% | 3.53% | 0.561 | −5.81% |

All figures include the same simulated **10 bp per dollar bought or sold**, including the initial investment. Traded fraction is the sum of absolute target-minus-drifted weights, with no division by two. Net monthly return is `(1 - 0.001 × traded_fraction) × (1 + gross_return) - 1`.

Annual Sharpe is `sqrt(12) × mean(net_monthly_return - monthly_rf_proxy) / sample_std(net_monthly_return)`. The risk-free proxy uses the last available FRED DGS1MO yield strictly before each month: `annual_yield_percent / 100 × calendar_days / 365`. This is a yield-accrual proxy, not an observed T-bill total-return index.

Historical monthly 95% VaR is minus the fifth percentile of net monthly returns, using linear interpolation: **3.68%** for MVO. Maximum drawdown uses month-end compounded wealth, including initial capital. The separate **current normal-model VaR is 3.80%**, calculated as `1.64485 × current_estimated_annual_volatility / sqrt(12)` with zero mean. Neither VaR is a maximum possible loss.

## What the backtest can and cannot establish

- The final weights use October 2021–September 2026 data, which overlap the evaluation period. The main test is **retrospective**, not an untouched out-of-sample test.
- Historical performance also informed ETF and model selection. No historical segment was kept untouched throughout that process.
- The two historical-fit checks estimate different weights before their subsequent evaluation periods. They exclude future returns from the numerical fit, but remain conditional on retrospectively selected ETFs and policies. Their results are separate from the main fixed-allocation figures.
- The six-ETF risk-parity benchmark has 3.75% current estimated volatility, below the challenge band. This does not imply every possible risk-parity portfolio would be below the band.
- The MVO Sharpe advantage over equal weight is modest. The bootstrap interval does not correct for model-selection bias, and the code does not produce a statistically justified Sharpe haircut or a guaranteed drawdown ceiling.
- The retained, overlapping research studies are recorded in [Results/research_variations.csv](Results/research_variations.csv). Their counts cannot simply be added; the file is not an exhaustive audit of every teammate’s experiments. Paths in that ledger refer to the original research archive, which is not included here.

Public adjusted-price data and source labels are preserved; **these are not Bloomberg historical data**. Any later reconciliation, updated data or changed allocation should be versioned separately rather than silently replacing this snapshot.
