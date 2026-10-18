# Challenge performance

The homepage reads `dist/data/challenge-valuations.csv`. The user confirmed inception at the 16 October 2026 close using the share quantities and prices in Round 1 positions.json. Holdings plus USD 12.12 cash reconcile to USD 100,000,000. The opening observation is recorded; subsequent valuations are not yet available. No additional fee deduction has been assumed.

Record verified end-of-day total USD portfolio values, including cash, in chronological order, one per date:

    date,nav_usd,source

The source field identifies the valuation source and must not contain commas. NAV must include dividend cash, actual fees and all holdings consistently. Rebalances do not restart the series. Do not add estimated or backtest observations here. Keep evidence for each valuation with the research records.

Performance is NAV / opening NAV minus one; the chart is indexed to 100 at inception. This assumes no external deposits or withdrawals. If capital is added or withdrawn, implement cash-flow-adjusted performance before publishing those observations. Dividends are internal portfolio flows, not external deposits. The daily workflow below refreshes public-price estimates; verified Bloomberg exports can be used separately to reconcile them.

Historical comparison data remains separate in performance-preview.js on the Round 1 page, derived from Results/main_monthly_returns.csv: Existing weights on Bloomberg data and Fixed equal weight. It must never be used as live challenge performance.

## Daily price updates

`update-prices.yml` runs at 23:37 UTC Monday–Friday (19:37 New York in summer; 18:37 in winter). GitHub schedules may be delayed. Scheduling activates only once the workflow is on the default branch. Manual runs on a preview branch update only that branch and never deploy Pages.

The updater uses the separately frozen `opening-positions.json` so research optimizations cannot silently change live holdings. It downloads Yahoo daily closes with automatic dividend adjustment disabled, values the fixed share quantities and adds distributions since inception as ex-date receivables without reinvestment. This is an estimated total portfolio value, not an official Bloomberg feed or a paid-cash ledger. No cash interest, taxes or unrecorded fees are assumed.

Splits cause a safe failure requiring reconciliation because vendor historical prices may be split-adjusted. Missing prices, differing ETF date coverage, invalid currency, stale data or failed downloads preserve the existing published series. Weekends and exchange holidays add no synthetic observations. Subsequent rebalance trades must be incorporated into the tracking ledger before they can be valued correctly; this first version tracks the confirmed opening holdings only.

Run `python scripts/update_challenge_prices.py` to refresh and `python -m unittest discover -s tests -p 'test_challenge_prices.py'` to verify accounting. The workflow explicitly invokes the Pages deployment after a successful main-branch update because commits made with GITHUB_TOKEN do not trigger another push workflow. The website always shows the latest valuation date.
