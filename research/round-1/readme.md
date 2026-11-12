# Round 1 portfolio analysis

Open `round1_analysis.ipynb` for the allocation method, formulas, input charts, portfolio comparisons, an estimated efficient frontier, stress summaries, expected shortfall and share quantities. Select Restart Kernel and Run All to reproduce it. The saved notebook includes the results.

`supplementary_studies.ipynb` contains constraint sensitivity, data-source comparisons, earlier fitting windows, cost sensitivity, Sharpe uncertainty, the frontier weights, 32 return-input scenarios, detailed stress contributions, expected shortfall, the impact of weight changes, rolling volatility, linked return attribution and the optional accounting reconciliation.

- `data/`: Bloomberg prices, the original export, FRED yields, earlier Yahoo prices and position quantities.
- `results/`: main calculation tables and charts. Charts are saved as PNG and PDF for use in the report.
- `studies/`: supporting calculation tables and charts.

Open Jupyter from this folder so the relative paths resolve. From the repository root, using the existing environment on this Mac:

```bash
conda activate base
cd research/round-1
jupyter lab
```

Run `round1_analysis.ipynb` first, then `supplementary_studies.ipynb`. Each can also run independently from the saved repository inputs. Package requirements are in [requirements.txt](requirements.txt). Rerunning refreshes tables and charts in `results/` and `studies/`; PDF metadata can change when a chart is regenerated.

Both notebooks passed a fresh-kernel check on **12 November 2026**: 28 and 45 code cells respectively, with zero errors and no external project files or data downloads.

## Final submission materials

The [submission folder](submission/readme.md) contains the submitted report, latest shared presentation, printable speaking notes and complete LaTeX projects for both documents, including fonts, logo and figures. See [Rebuilding the reports and slides](../documents.md) for the single build command. The report has 13 pages and the presentation has 16.
