# Input data

The source snapshot comes from the AMC Team Pack dated 14 October 2026. Yahoo Finance ETF responses were retrieved on 13 October; exact URLs and retrieval timestamps are listed in [sources.json](sources.json). The original team pack retains the full Yahoo JSON responses. This repository includes the derived monthly series needed by the scripts and the raw FRED CSV used by the verifier.

| File | Contents |
| --- | --- |
| `month_end_prices.csv` | Adjusted USD prices at complete month ends. These are research inputs, not official challenge execution prices. |
| `monthly_returns.csv` | Simple returns derived from consecutive adjusted month-end prices. The common eight-ETF history runs from November 2011 to September 2026. |
| `current_60_month_returns.csv` | The current fitting window, October 2021–September 2026. |
| `annual_covariance.csv` | Sample monthly covariance multiplied by 12, retained as a reference table. |
| `correlations.csv` | Sample monthly return correlations, retained as a reference table. |
| `risk_free_monthly.csv` | FRED DGS1MO observation dates, annual percentage yields, calendar days and derived monthly yield-accrual proxies. |
| `Raw sources/FRED_DGS1MO.csv` | The daily Treasury-yield source used to verify the monthly risk-free conversion. |
| `sources.json` | ETF source URLs and retrieval timestamps, plus the FRED source and conversion convention. |

Returns, covariance entries, weights and risk shares are decimals: `0.2608` means 26.08%. The `annual_yield_percent` column instead uses percentage points: `4.0` means 4% annually. Dates label return months or source observations as indicated by their columns.

The current optimizer reads `monthly_returns.csv` and selects its last 60 rows; it recalculates means and covariance rather than relying on the reference covariance CSV. Prices are adjusted-price total-return proxies incorporating distributions and splits. No additional dividend return is added, and fund expenses are not deducted a second time.

The saved dataset contains SPY, VWO, EEMV, DBC, XLE, SCHD, VGSH and STIP. The optimizer excludes XLE; VWO receives zero weight. The main backtest compares the six held ETFs only.

Sources: [Yahoo Finance](https://finance.yahoo.com/) and [FRED DGS1MO](https://fred.stlouisfed.org/series/DGS1MO). This snapshot does not contain Bloomberg exports.
