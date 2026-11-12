# Shared valuation calculations

The companion notebook imports four small modules:

- `portfolio_inputs.py`: saved prices, statements, source corrections, regressions and original valuation assumptions.
- `valuation.py`: FCFF/WACC, financing-consistent FCFE, reverse valuation, holding-period cash flows and fixed-portfolio sensitivities.
- `replay_methods.py`: staggered holding periods, non-overlapping offsets, block bootstrap and chronological risk estimates.
- `valuation_validation.py`: reruns those tests for the agreed weights, entered holdings, SAA and simple controls.

All data comes from the repository. No live downloads or trading calls are made. Monetary company inputs use USD millions; per-share prices use USD. The original EPS/P-E selection and the conservative cash-flow sensitivity remain distinct. The additional [beta and dividend checks](../post-submission/readme.md) use these shared inputs and valuation functions from separate scripts; they are labelled as post-submission work.
