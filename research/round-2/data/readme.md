# Frozen input provenance

Price cutoff: 6 November 2026. Risk calibration: 60 complete monthly USD returns, November 2021–October 2026. These files preserve the inputs used for the final Checkpoint 2 research, not live market observations.

- `prices/`: raw Yahoo chart responses for the six benchmark ETFs and nine eligible researched stock cases. Raw closes are used for quantities; adjusted closes for historical returns.
- `price_fallback/`: archived supplementary price histories, used only where the primary series is missing observations.
- `statements/`: annual and quarterly statement observations for the researched companies. `annual_statements.csv` also contains the archived peer observations needed for the six value-trap ratios. Fiscal dates and accounting bases remain explicit.
- `quotes*.json`: frozen quote snapshots used for share counts and cash-per-share calculations; they are not the final execution price source.
- `issuer_overrides.json`, `dividend_overrides.json`: explicit source corrections. The notebook applies them transparently.
- `fred_history.csv`: archived rate observations; monthly mean DGS1MO divided by 1200 is the monthly risk-free proxy.
- `policies/`: valuation assumptions, implementation rules and qualitative company notes. These are research judgements, not observed prices or fitted historical alphas.
- `peer_sets.json`, `researched_universe.json`: peer definitions and the nine eligible researched company cases. This is not a point-in-time historical stock universe or a global exhaustive search.
- `sources.json`: the primary issuer/source register used in the report. Course requirements are summarised in the notebook; course handouts and private team conversations are omitted.

The notebook independently recalculates valuations, alpha scores, weights, risk and replay statistics. Saved JSON results are used for final-case reconciliation and the explicitly labelled earlier funding comparison. They are not substituted for those calculations. `input_manifest.json` records SHA-256 hashes of the frozen inputs. No data refresh is performed when running the notebook.
