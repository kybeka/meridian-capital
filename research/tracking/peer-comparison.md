# Peer comparison preview

The comparison reconstructs Meridian, Sixfold, SwissStreet, Matterhorn and Rivemont from their published Round 1 share quantities. It is an estimate of unchanged opening baskets, not an official challenge ranking. Source URLs and the holdings-review date are recorded in `peer-positions.json` and exposed beside the chart.

All start at the 16 October 2026 close. Prices use the existing Yahoo daily-close downloader; distributions accrue as ex-date receivables without reinvestment. Cash earns zero. Fees and taxes are excluded. The chart divides each portfolio by its own opening basket value and multiplies by 100. It plots only actual daily observations; hover snaps to the closest observation.

## Source checks on 29 October 2026

- Sixfold: downloaded its public portfolio-description CSV; six quantities, prices and $673.18 cash reconcile exactly to $100 million.
- SwissStreet: five quantities, opening prices and $90.04 cash from its published Table 6.1 reconcile exactly.
- Matterhorn: eight nonzero positions and $5.22 cash from its public `data/holdings.json`. The file specifies $100 million and 16 October inception but omits opening prices. Yahoo closing prices rounded to cents reconcile these quantities and cash exactly to $100 million. Its zero-share BIL row is omitted.
- Rivemont: six quantities, entry prices and $667 cash from its performance page. Cash is published to whole dollars: the opening basket is $100,000,000.08. Preserve that rounding and normalize by that basket value; do not invent an eight-cent cash adjustment.
- Meridian: use the existing confirmed opening-positions file. Its comparison line matches its existing tracker to display precision.

Published prices are checked against the common price feed within $0.011 per share. Missing prices, mismatched dates, splits, unreconciled opening capital, stale responses and backward date changes fail without replacing saved peer data. Updating peer data is independent of the main Meridian updater, so peer failures cannot stop the existing tracker.

Run `python scripts/update_peer_prices.py` to refresh. For a reproducible check, pass `--history-file PATH` with previously downloaded downloader responses. Run `python -m unittest discover -s tests -p 'test_*prices.py'`.

The current verification covers opening holdings only. The generator stops at the first-round closing date, 6 November 2026. Verify new trades and implement a dated trade ledger before extending beyond that date. No automatic scraping of later holdings is performed.
