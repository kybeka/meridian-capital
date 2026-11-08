# Round 2 results

The CSV tables and PNG charts are snapshots from the complete execution of `../round2_analysis.ipynb` with the unchanged final controls. They make the results accessible without opening Jupyter. Editing notebook assumptions does not overwrite these snapshots; the displayed notebook output is the result for that edited scenario.

- `company_valuations.csv`, `alpha_and_residual_risk.csv`, `value_trap_checks.csv`: valuation, forecast and quality calculations.
- `candidate_portfolios.csv`, `portfolio_comparison.csv`, `portfolio_risk.csv`, `requirements_and_preferences.csv`: all 420 candidates, the selected comparisons, four risk estimates and rule/preference checks.
- `staggered_summary.csv`, `nonoverlapping_offsets.csv`: holding-period summaries and the number of non-overlapping observations at each offset.
- `forward_risk_tests.csv`, `forward_risk_summary.csv`, `matched_monthly_risk_tests.csv`: chronological training/test risk comparisons. These use fixed current portfolio weights, not a historical point-in-time stock-selection process.
- `round1_attribution.csv`, `round1_nav.csv`, `final_positions.csv`: realised Round 1 reconstruction and the final zero-fee implementation.
- `nav_dividends.csv`, `nav_reconciliation.csv`: the issuer-verified VGSH/STIP distributions and the components of the 6 November NAV. The website updater uses the same events and closing-price precision.
- Five PNG charts: Round 1 performance, residual correlations, capital allocation, recent staggered replays and forward risk validation.
- `notebook_verification.json`: execution outcome and file-integrity checks.
- `valuation/`: completed cash-flow valuations, financing schedules, implied growth, convergence returns, sensitivities and repeated portfolio tests. The companion notebook recomputes the valuations and refreshes the test summaries. Its raw 18 MB replay file is generated locally and excluded from Git.
- `workbook_style_verification.json`: checks that the Excel wording/style edits preserve numeric inputs, formulas, cached results and nine native two-input sensitivity tables.

The JSON files preserve compact final-release reference results used for explicit reconciliation assertions and the earlier funding comparison. The notebook independently recomputes the central calculations; it does not use these saved outputs as a substitute for valuation, weighting, risk or replay calculations. The larger development archive and duplicate intermediate histories are omitted from this repository layout.
