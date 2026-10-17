# Challenge performance

The homepage reads `dist/data/challenge-valuations.csv`. The user confirmed inception at the 16 October 2026 close using the share quantities and prices in Round 1 positions.json. Holdings plus USD 12.12 cash reconcile to USD 100,000,000. The opening observation is recorded; subsequent valuations are not yet available. No additional fee deduction has been assumed.

Record verified end-of-day total USD portfolio values, including cash, in chronological order, one per date:

    date,nav_usd,source

The source field identifies the valuation source and must not contain commas. NAV must include dividend cash, actual fees and all holdings consistently. Rebalances do not restart the series. Do not add estimated or backtest observations here. Keep evidence for each valuation with the research records.

Performance is NAV / opening NAV minus one; the chart is indexed to 100 at inception. This assumes no external deposits or withdrawals. If capital is added or withdrawn, implement cash-flow-adjusted performance before publishing those observations. Dividends are internal portfolio flows, not external deposits. Uploading a revised CSV updates the site through the normal deployment; this does not fetch Bloomberg or market data automatically.

Historical comparison data remains separate in performance-preview.js on the Round 1 page, derived from Results/main_monthly_returns.csv: Existing weights on Bloomberg data and Fixed equal weight. It must never be used as live challenge performance.
