# Additional data for the 10 November checks

The beta audit needs historical prices for the peers listed in `../peer_sets.json`. Seventeen extra Yahoo chart responses are saved in `peer_prices/`. INTU and GILD already have histories in `../prices/`, which the audit reuses.

[peer_price_manifest.json](peer_price_manifest.json) records the paths, SHA-256 hashes, original request URLs and retrieval timestamps for all 19 series. The extra files are unchanged copies of archived research inputs. The peer regressions stop at October 2026 and use the same 60 monthly dates as the stock/SPY regressions.

These files were added with the post-submission audit on 12 November. They are kept separately from the original submission's price folder and input manifest. The original notebooks do not use them. The audit verifies their hashes before running and makes no network requests.

The DDM checks use the existing saved valuation inputs and require no additional data.
