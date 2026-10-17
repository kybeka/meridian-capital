# Round 1 website verification

The dedicated website page uses the agreed allocation with Bloomberg ETF inputs, not the separately reoptimized candidate and not the original public-data backtest. Original files in this research directory remain the earlier public-data release.

## Rerun

A fresh isolated output directory, `outputs/Round 1 website verification 2026-10-17`, was created alongside the existing team pack outside this repository. The original source workbook and team release were left unchanged. Using the existing Conda base environment (NumPy 2.1.3, pandas 2.2.3, SciPy 1.15.3, openpyxl 3.1.5), the following were executed:

1. `Code/revalidate_bloomberg.py`: source workbook extraction, 200 optimizer starts, implementable rounding, four fixed-weight backtests and independent dollar accounting.
2. `Code/backtest.py`: additional historical fits, cost sensitivity and bootstrap calculations. Its MVO row uses the reoptimized candidate; it is not the website's agreed-weight row.
3. `Code/verify_backtest.py`: independent source-price returns, risk-free conversion and dollar-accounting reconciliation for 891 strategy-month observations.
4. `scripts/verify_round1.py <rerun-directory>` from this repository: independent agreed-weight covariance/risk checks and comparison of the actual HTML chart/table values with fresh results. Generates the downloadable CSV and verification JSON in `dist/research/`.

The current Bloomberg rerun script expects the supplied `AMC Bloomerg Data.xlsx` and its sibling `AMC Team Pack 2026-10-14`. It is an existing local research workflow, not a self-contained public-data reproduction. Bloomberg source prices have not been added to this repository. The verification JSON identifies the source workbook by SHA-256.

## Findings

All displayed numeric values match the fresh Bloomberg rerun at shown precision. Agreed weights pass all capital, minimum-exposure, volatility and risk-share limits. The independently rebuilt agreed-weight annual volatility is 7.9989949596%.

| Portfolio | CAGR | Annual volatility | Sharpe | Maximum month-end drawdown |
| --- | ---: | ---: | ---: | ---: |
| Agreed MVO | 9.040017% | 8.600247% | 0.768120 | -16.189560% |
| Equal weight | 8.490131% | 8.300204% | 0.731379 | -15.166995% |
| Risk parity | 4.458461% | 3.531645% | 0.561212 | -5.806619% |

Historical monthly 95% VaR is 3.684004%; current zero-mean normal-model monthly 95% VaR is 3.798150%. All are retrospective research calculations, not live challenge returns.

## Wording corrections

- Link the page to fresh Bloomberg-derived summary results rather than solely to older public-data outputs.
- Identify risk-parity fitting, fixed target weights and equal-weight comparator construction.
- State the precise pre-fee turnover cost convention; it is not a trade-by-trade execution model.
- Avoid claiming all original dividend-adjustment requests were independently visible. Only SPY's request settings are preserved in the supplied workbook.
- Preserve estimation/evaluation windows, overlap/selection limitations, and the distinction between an agreed allocation and a reoptimized candidate.

No publication/snapshot date is displayed on the research page. The calculation windows remain visible. No allocation or live holdings changes are implied by this audit.
