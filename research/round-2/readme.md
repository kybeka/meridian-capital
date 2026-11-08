# Round 2 portfolio analysis

Open [round2_analysis.ipynb](round2_analysis.ipynb) for the complete Checkpoint 2 walkthrough: Round 1 performance, the post-loss budget, company valuations and catalysts, forecast alphas, stock weights, information ratio, portfolio comparisons, risk checks, staggered replays and final share quantities. Saved outputs are included. Select **Restart Kernel and Run All** to reproduce them.

The layout follows [Round 1](../round-1/readme.md): one main notebook, frozen inputs, ordinary result tables and final deliverables. Clone or download the repository before running; downloading only the notebook omits its data. Open Jupyter from this folder or the repository root. Dependencies tested in the existing Python 3.13 conda environment are listed in [requirements.txt](requirements.txt).

- [data/](data/readme.md): archived prices, statements, rate observations, source corrections, valuation assumptions, company notes and source register. An input manifest records SHA-256 hashes.
- [results/](results/readme.md): calculation tables, charts, frozen comparison results and execution checks. Percentages in CSV files are decimal fractions unless the column says otherwise.
- [submission/](submission/readme.md): the final report and Excel model, preserved byte for byte from the verified release.

## The decision

The original six-ETF SAA remains the benchmark. Our funding choice scales each ETF target to two-thirds and allocates one-third of the **post-loss** portfolio value to **ADBE, KR, HRL, BMY, XOM and HPQ**. Stock proportions follow positive forward alpha divided by residual variance. Selection is explained using information ratio; Sharpe reporting and the theoretical SAA link are separate supplementary calculations.

The frozen price cutoff is **6 November 2026**. Calibration uses **60 complete monthly USD returns, November 2021–October 2026**. The one-third requirement is a class instruction reported by the team. The written tracking-error convention is distinguished from additional daily-risk and concentration preferences in the notebook.

Implementation uses **zero fees and no reserve**. The verified closing-price NAV is **$97,115,068.58**, including the VGSH and STIP distributions paid before 6 November; the one-third stock budget is **$32,371,689.53**. The final share counts include the additional SPY and Adobe purchases reported by the team: **22,964 SPY**, **18,865 ADBE**, and **$116.05 residual cash**. The notebook reconciles all twelve quantities with the saved Excel model and verifies the report/model hashes. The [cross-artifact reconciliation](../tracking/nav-reconciliation-2026-11-06.json) checks these figures against the website; [issuer evidence](../tracking/dividend-evidence/verification.json) records the distribution amounts and dates.

## What the evidence supports

The notebook enumerates all 420 combinations of three to six names within the nine positive-alpha researched cases. Six stocks have a slightly lower full-residual IR than the five-stock maximum, but lower recent tracking error and concentration. This is a documented tradeoff within the researched universe, not a claim of a global optimum.

Official monthly TE is approximately **3.92%**, within the 2–5% band. The additional daily 5% TE preference and 8% individual-stock preference do not both pass. Staggered replays do **not** establish historical outperformance: the selected six have negative average recent active return. Overlapping starts are dependent, and the tests reuse a present-day universe and researched assumptions. Forward risk checks reveal that monthly estimates can understate subsequent daily risk. These findings remain visible throughout the notebook and report.

Default execution uses frozen inputs, makes no network requests and does not change the final report or workbook. Editable assumptions create a labelled research scenario; they do not automatically supply a revised investment thesis or become a new submission. This folder contains research and the team's reported implementation, not an independent live Bloomberg holdings feed.
