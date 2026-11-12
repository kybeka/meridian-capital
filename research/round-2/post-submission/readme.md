# Checks after submission

We ran these checks on **10 November 2026**, following questions about our discount rates and dividend assumptions. They use the saved **6 November** valuation inputs. We added them to the repository on 12 November. The submitted report, workbook, notebooks and share quantities are unchanged.

## Beta and discount rates

[beta-discount/audit.py](beta-discount/audit.py) reproduces the six submitted market betas and cash-flow values, then checks how much those estimates depend on the sample and discount rate.

- Regress monthly stock excess returns on SPY excess returns over November 2021–October 2026, with an intercept. Report ordinary least squares (OLS) standard errors and Newey–West errors with three lags, plus approximate 95% intervals.
- Compare the first and last 30 months, the last 36 and 24 months, weekly returns over approximately the same period, and the latest 252 daily returns. The daily comparison also changes the lookback.
- Compare betas against the original mixed-asset strategic asset allocation (SAA) and against SPY. The valuation's equity risk premium is measured against the equity market, so its CAPM beta uses SPY. The SAA beta describes exposure to our portfolio benchmark.
- Raise the cost of equity by one and two percentage points and recalculate the weighted average cost of capital (WACC). Keep cash flows, growth, debt cost and balance-sheet inputs fixed.
- Find the discount rate at which cash-flow value equals the entry price. Also try one-third shrinkage of beta toward 1 and each company's raw peer median beta.

The script checks all 18 base/+1pp/+2pp cash-flow values against the saved submission results. It also verifies the archived peer-price hashes and 60 observations for each of the 19 peer regressions.

| Stock | SPY beta, 60 months | Base cash-flow value | Cost of equity +1pp | Cost of equity +2pp | Entry price |
| --- | ---: | ---: | ---: | ---: | ---: |
| ADBE | 1.365 | $271.14 | $245.93 | $224.90 | $239.30 |
| KR | 0.361 | $87.45 | $71.10 | $58.85 | $67.70 |
| HRL | 0.274 | $31.49 | $25.53 | $21.30 | $21.95 |
| BMY | 0.212 | $65.50 | $55.72 | $48.08 | $62.14 |
| XOM | 0.172 | $213.08 | $168.61 | $139.08 | $165.87 |
| HPQ | 1.181 | $34.44 | $30.61 | $27.44 | $28.46 |

These are the cash-flow cross-checks; the submitted earnings-based targets are shown in the dividend table below. BMY has little room for a higher discount rate: its cash-flow value reaches entry at about 6.08% WACC, compared with 5.83% in the base case. XOM's beta varies sharply across samples. The audit gives us less confidence in treating a low estimated beta as a stable measure of risk.

Peer medians and shrinkage are sensitivity assumptions. The peer betas have not been adjusted for leverage, cash or business mix. The regression intervals describe estimation uncertainty in historical beta; they do not provide a range for future fair value.

Files:

- [beta_diagnostics.csv](beta-discount/beta_diagnostics.csv): sample comparisons, uncertainty intervals and break-even rates for six stocks.
- [discount_rate_scenarios.csv](beta-discount/discount_rate_scenarios.csv): five valuation scenarios per stock.
- [peer_beta_diagnostics.csv](beta-discount/peer_beta_diagnostics.csv): 19 peer regressions.
- [audit_metadata.json](beta-discount/audit_metadata.json): dates, input hashes and calculation checks.

## Dividend discount models

[ddm/ddm_checks.py](ddm/ddm_checks.py) values the five dividend-paying stocks using the Gordon dividend discount model (DDM), plus a five-year two-stage model. Adobe pays no dividend in our saved inputs and is excluded.

For constant growth, `D1 = D0 × (1 + g)` and `value = D1 / (k − g)`. Here `D0` is the saved current annualized dividend per share, `g` is assumed dividend growth and `k` is the submitted cost of equity. Payments are approximated annually. The five-year model discounts each dividend and a Gordon terminal value at year five.

We test 0–3% constant growth, the saved dividend-growth assumption, five flat years followed by 2% growth, an immediate 25% dividend cut, and higher costs of equity. We also solve for the perpetual growth needed to reach the entry price and submitted target.

| Stock | Entry price | Submitted P/E target | DDM, 2% growth | DDM, 2% growth and equity cost +1pp | Growth needed for target |
| --- | ---: | ---: | ---: | ---: | ---: |
| KR | $67.70 | $78.00 | $31.53 | $26.31 | 4.95% |
| HRL | $21.95 | $25.16 | $26.41 | $21.63 | 1.78% |
| BMY | $62.14 | $70.95 | $62.15 | $50.05 | 2.50% |
| XOM | $165.87 | $180.00 | $112.24 | $89.29 | 3.43% |
| HPQ | $28.46 | $32.13 | $12.16 | $11.07 | 8.03% |

At 2% growth, Hormel's dividend value exceeds our submitted target, although a one-point increase in the cost of equity puts it slightly below entry. BMY's value is close to entry. Its saved assumption was 0% dividend growth, which gives $41.07. The other saved growth assumptions were 2%.

The 2% assumption is a common comparison scenario. We have not independently forecast that growth for every company. The implied growth column shows what the target requires; it does not establish that the company can deliver it. These results also retain the original cost-of-equity uncertainty.

A model based on current dividends can give low values for companies that return cash through buybacks or retain it for investment. We have not forecast changes in payout ratios or share counts here. Buybacks, cash and retained earnings are not added separately to the DDM. The Gordon formula used for the submitted cash-flow model's terminal value did not constitute a standalone dividend valuation; these DDM checks were additional work after submission.

Files:

- [ddm_summary.csv](ddm/ddm_summary.csv): inputs, values and implied growth for five stocks.
- [ddm_scenarios.csv](ddm/ddm_scenarios.csv): nine scenarios per stock.
- [methodology.json](ddm/methodology.json): input hash, conventions and arithmetic checks.

## Rerun from saved data

Use the Round 2 [Python dependencies](../requirements.txt). From the repository root:

```bash
python research/round-2/post-submission/beta-discount/audit.py
python research/round-2/post-submission/ddm/ddm_checks.py
```

Both scripts work offline and write their CSV and JSON outputs beside the script. They read the submitted inputs under `results/valuation/` and the archived data under `data/`. Extra peer prices and their source dates are in [data/post-submission/](../data/post-submission/readme.md). No live-price refresh is performed.
