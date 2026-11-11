# Challenge performance

The homepage reads `dist/data/challenge-valuations.csv`. The user confirmed inception at the 16 October 2026 close using the share quantities and prices in `opening-positions.json`. Holdings plus USD 12.12 cash reconcile to USD 100,000,000. Valuations through 6 November are reconstructed from this fixed opening book. No additional fee deduction has been assumed.

Record verified end-of-day total USD portfolio values, including cash, in chronological order, one per date:

    date,nav_usd,source

The source field identifies the valuation source and must not contain commas. NAV must include dividend cash, actual fees and all holdings consistently. Rebalances do not restart the series. Do not add estimated or backtest observations here. Keep evidence for each valuation with the research records.

Performance is NAV / opening NAV minus one; the chart is indexed to 100 at inception. This assumes no external deposits or withdrawals. If capital is added or withdrawn, implement cash-flow-adjusted performance before publishing those observations. Dividends are internal portfolio flows, not external deposits. The daily workflow below refreshes public-price estimates; verified Bloomberg exports can be used separately to reconcile them.

Historical comparison data remains separate in performance-preview.js on the Round 1 page, derived from Results/main_monthly_returns.csv: Existing weights on Bloomberg data and Fixed equal weight. It must never be used as live challenge performance.

## Daily price updates

`update-prices.yml` runs at 23:37 UTC Monday–Friday (19:37 New York in summer; 18:37 in winter). GitHub schedules may be delayed. Scheduling activates only once the workflow is on the default branch. Manual runs on a preview branch update only that branch and never deploy Pages.

The updater uses the separately frozen `opening-positions.json` so research optimizations cannot silently change live holdings. It downloads Yahoo daily closes with automatic dividend adjustment disabled, rounds closing prices to cents consistently with the Checkpoint 2 reconstruction, values the fixed share quantities and adds distributions since inception as ex-date receivables without reinvestment. After payment those entitlements represent cash; they are not added a second time. This is an estimated total portfolio value, not an official Bloomberg feed or a paid-cash ledger. No cash interest, taxes or unrecorded fees are assumed.

`verified-distributions.json` preserves issuer-confirmed events omitted from the vendor history. A matching vendor event is counted once; a conflicting amount stops publication. Vanguard confirms VGSH's 2 November ex-date payment of USD 0.1889 per share, paid 4 November; iShares confirms STIP's USD 0.292917 per share, paid 5 November. The original holdings were entitled to USD 100,916.78561 in total. The October VGSH distribution is outside this portfolio's entitlement window and is not credited. See `dividend-evidence/` for the verification record and `nav-reconciliation-2026-11-06.json` for the cross-artifact reconciliation. The closing-price NAV is USD 97,115,068.58; this is not an independent confirmation of Bloomberg's booked cash or tax treatment.

Splits cause a safe failure requiring reconciliation because vendor historical prices may be split-adjusted. Missing prices, differing ETF date coverage, invalid currency, stale data or failed downloads preserve the existing published series. Weekends and exchange holidays add no synthetic observations. Subsequent rebalance trades must be incorporated into the tracking ledger before they can be valued correctly; this first version tracks the confirmed opening holdings only.

Run `python scripts/update_challenge_prices.py` to refresh and `python -m unittest discover -s tests -p 'test_challenge_prices.py'` to verify accounting. The workflow explicitly invokes the Pages deployment after a successful main-branch update because commits made with GITHUB_TOKEN do not trigger another push workflow. The website always shows the latest valuation date.

## Round 2 tracking (11 November 2026)

`round2-positions.json` records the submitted twelve-position portfolio: entry on
7 November at 6 November closing prices and $116.04561 residual cash (displayed
as $116.05). The submitted position values plus cash equal $97,115,068.57561.
The original opening snapshot is retained. The daily updater uses Round 1
shares through the 6 November close and Round 2 shares thereafter. November
VGSH and STIP distributions are already in the rebalance cash budget; they are
credited once. Later ex-date entitlements use the shares held in the new round.
The calculation rejects an unexplained rebalance NAV difference above one cent.

`portfolio-contributions.json` contains daily and cumulative contributions for
all twelve instruments. Cumulative contributions carry each holding's dollar
P&L across the rebalance, divided by the original $100m. Daily contributions use
the previous close's NAV. This preserves pre-sale gains/losses and attributes
new stock returns only after entry. The former Round 1 contribution file is
retained as a historical export, while the homepage reads the new file.

`peer-round2-positions.json` records the four teams' public share counts and cash,
verified on 11 November. Source URLs are recorded with each snapshot. All four
use the 6 November closing-price basis. Matterhorn publishes quantities and
cash; its snapshot prices were taken from the same daily-price feed and rounded
to cents. Its basket differs from stated capital by $0.08; Rivemont's by $0.39,
within the existing $1 tolerance for published rounding.

`peer-distributions.json` supplements vendor events with documented November
distributions. It distinguishes issuer, peer-reported Bloomberg, and cross-checked
public distribution sources. Conflicting vendor amounts fail validation rather
than being silently overwritten. These additions also improve the historical
peer comparison, where the vendor had omitted November bond ETF distributions.

Peer Round 2 returns are linked to the reconstructed Round 1 closing index.
This avoids treating differences in published cash/NAV conventions as investment
returns. Each series records the unscaled basket, reconstructed NAV and difference
in `rebalance_reconciliation`. Meridian uses its reconciled continuous dollar NAV
in both chart views. Team A–D display labels are preserved.

Daily prices refresh through the existing weekday workflow. Holdings change only
when a new confirmed snapshot is added. Public prices and dividend treatment can
differ from Bloomberg's official performance; cash earns zero, with no fees or taxes.

For a reproducible local run, pass a JSON mapping of ticker to `closes`,
`dividends` and `splits` to either updater's `--history-file` option. Tests cover
rebalance continuity, changed-share dividend entitlement, P&L attribution,
missing boundary prices and peer return linking.
