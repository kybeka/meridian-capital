# Data sources

The active ETF source is Raw sources/AMC Bloomerg Data.xlsx. The export is preserved unchanged. October 2011–September 2026 provides 180 prices and 179 monthly returns. Import code corrects the first date to 31 October 2011 following user confirmation. SPY adjustment flags are preserved; the other ETF columns were supplied as saved values.

Top-level CSVs are generated from Bloomberg. Actual source dates are retained separately; analysis dates are normalized to month-end without interpolation. risk_free_monthly.csv remains the FRED DGS1MO yield-accrual proxy, checked against its raw source CSV.

Archive Yahoo 2026-10-14 contains the older public-data snapshot for provenance, not current input.
