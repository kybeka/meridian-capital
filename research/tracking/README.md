# Challenge performance

The homepage reads `dist/data/challenge-valuations.csv`, `dist/data/portfolio-contributions.json` and `dist/data/peer-valuations.json`. The tracker uses the confirmed opening holdings through the 6 November close, then the submitted Round 2 holdings. Both snapshots are saved in this folder. The opening quantities and USD 12.12 cash reconcile to USD 100,000,000. No fees, taxes or cash interest are assumed.

The daily updater writes one estimated total USD portfolio value per completed trading date, in chronological order:

```csv
date,nav_usd,source
```

The series includes holdings, cash and distribution receivables. Rebalances do not restart it. The source column identifies the public-price reconstruction; Bloomberg exports can be retained as separate reconciliation evidence. Historical backtest values belong in the research results.

Performance is NAV / opening NAV minus one; the chart is indexed to 100 at inception. This assumes no external deposits or withdrawals. If capital is added or withdrawn, implement cash-flow-adjusted performance before publishing those observations. Dividends are internal portfolio flows, not external deposits. The daily workflow below refreshes public-price estimates; verified Bloomberg exports can be used separately to reconcile them.

The historical comparison on the Round 1 page uses `dist/performance-preview.js`. Its backtest methodology and saved tables are described in [the Round 1 research folder](../round-1/readme.md). This historical chart remains separate from the challenge tracker.

## Daily price updates

[The price-update workflow](../../.github/workflows/update-prices.yml) runs at 23:37 UTC Monday–Friday (19:37 New York in summer; 18:37 in winter). GitHub schedules may be delayed. Scheduled runs use the default branch. Manual runs on a preview branch update only that branch and do not deploy Pages.

The updater uses the saved `opening-positions.json` and `round2-positions.json` snapshots, so rerunning a research optimization does not change the tracked holdings. It downloads Yahoo daily closes with automatic dividend adjustment disabled, rounds closing prices to cents consistently with the Checkpoint 2 reconstruction, values the shares held in each round and adds the corresponding ex-date distribution entitlements without reinvestment. After payment those entitlements represent cash; they are not added a second time. This is an estimated total portfolio value, not an official Bloomberg feed or a paid-cash ledger. No cash interest, taxes or unrecorded fees are assumed.

`verified-distributions.json` preserves issuer-confirmed events omitted from the vendor history. A matching vendor event is counted once; a conflicting amount stops publication. Vanguard confirms VGSH's 2 November ex-date payment of USD 0.1889 per share, paid 4 November; iShares confirms STIP's USD 0.292917 per share, paid 5 November. The original holdings were entitled to USD 100,916.78561 in total. The October VGSH distribution is outside this portfolio's entitlement window and is not credited. See `dividend-evidence/` for the verification record and `nav-reconciliation-2026-11-06.json` for the cross-artifact reconciliation. The closing-price NAV is USD 97,115,068.58; this is not an independent confirmation of Bloomberg's booked cash or tax treatment.

Splits cause a safe failure requiring reconciliation because vendor historical prices may be split-adjusted. Missing prices, differing ETF date coverage, invalid currency, stale data or failed downloads preserve the existing published series. Weekends and exchange holidays add no synthetic observations. Round 2 is incorporated as described below. Future rebalances require a confirmed holdings snapshot and an updater change before the new positions can be valued.

From the repository root, the commands below fetch new public prices and update the website data files:

```bash
python scripts/update_challenge_prices.py
python scripts/update_peer_prices.py
```

Run the accounting checks without fetching prices:

```bash
python -m unittest discover -s tests -p 'test_*prices.py'
```

The workflow explicitly invokes the Pages deployment after a successful main-branch update because commits made with GITHUB_TOKEN do not trigger another push workflow. The website always shows the latest valuation date.

## Round 2 holdings and contributions

`round2-positions.json` records the submitted twelve-position portfolio: entry on
7 November at 6 November closing prices and $116.04561 residual cash (displayed
as $116.05). The submitted position values plus cash equal $97,115,068.57561.
The original opening snapshot is retained. The daily updater uses Round 1
shares through the 6 November close and Round 2 shares thereafter. November
VGSH and STIP distributions are already in the rebalance cash budget; they are
credited once. Later ex-date entitlements use the shares held in the new round.
The calculation rejects an unexplained rebalance NAV difference above one cent.

`dist/data/portfolio-contributions.json` contains daily and cumulative contributions for
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
public distribution sources. Yahoo events that exactly match the documented amount rounded to three decimals
retain the documented full precision. Other conflicting vendor amounts fail validation. These additions also improve the historical
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
