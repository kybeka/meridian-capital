"""Build the Round 2 research page from the recorded portfolio and saved results."""

import argparse
import csv
import hashlib
import html
import json
import math
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'research/round-2'
DIST = ROOT / 'dist'
REPORT = 'materials/round-2-report.pdf'
MODEL = 'https://github.com/kybeka/meridian-capital/blob/main/research/round-2/submission/Meridian_Final_Model.xlsx'
CODE = 'https://github.com/kybeka/meridian-capital/tree/main/research/round-2'


def load(name):
    return json.loads((RESEARCH / name).read_text())


def pct(value, digits=2):
    return f'{value * 100:.{digits}f}%'


def money(value):
    return f'${value:,.2f}'


def heading(identifier, title, intro):
    return f'<div class="editorial-heading"><h2 id="{identifier}">{title}</h2><p>{intro}</p></div>'


def build(report_path):
    record = load('submission/submission_record.json')
    analysis = load('results/analysis.json')
    cash_values = {v['ticker']: v for v in load('results/valuation/valuations.json')}
    holdings = record['holdings']
    nav = record['nav_usd']
    with (RESEARCH / 'results/round1_attribution.csv').open() as f:
        attribution = list(csv.DictReader(f))
    windows = load('results/window_summary.json')
    replay = {regime: next(x for x in windows if x['candidate'] == 'Rebuild' and
                          x['horizon'] == 33 and x['regime'] == regime)
              for regime in ['pre', 'post']}
    peers = {v['ticker']: v for v in analysis['rows']}
    stock_names = {'ADBE': 'Adobe', 'KR': 'Kroger', 'HRL': 'Hormel Foods',
                   'BMY': 'Bristol Myers Squibb', 'XOM': 'ExxonMobil', 'HPQ': 'HP'}
    security_names = {'SPY': 'SPDR S&P 500 ETF', 'EEMV': 'iShares EM Min Vol ETF',
                      'DBC': 'Invesco DB Commodity ETF', 'SCHD': 'Schwab US Dividend ETF',
                      'VGSH': 'Vanguard Short-Term Treasury ETF', 'STIP': 'iShares 0–5 Year TIPS ETF',
                      **stock_names}
    cases = {
        'ADBE': ('Subscription cash flow supports the valuation. Our 16× GAAP earnings multiple allows for uncertainty over AI competition and renewals.',
                 '9 December: results and the first FY2027 outlook. We will watch renewals and paid AI revenue.',
                 'A 20% cut to normalized cash lowers the cash valuation to $216.54, below the $239.30 entry price.'),
        'KR': ('Grocery demand and cash generation support a 15× adjusted earnings multiple. Low residual risk gives Kroger the largest stock weight.',
               '3 December: results should show whether the fulfillment reset supports sales and margins.',
               'Buybacks exceed cash available without new debt. Thin margins and leverage limit the case.'),
        'HRL': ('The 17× adjusted earnings multiple assumes recovering margins. This is a premium to our food peers and needs support from results.',
                '3 December: the first FY2027 outlook under the new CEO, with dividend coverage and Retail volumes in focus.',
                'Acquisition debt tightens dividend coverage. Full refinancing in our funding stress leaves coverage close to one.'),
        'BMY': ('An 11× guided earnings multiple allows for the patent cliff. The flat-cash valuation gives a smaller cushion at $65.50.',
                'Pipeline readouts expected by year-end and ASH data on 12–15 December could improve confidence in replacement medicines.',
                'Trial outcomes are uncertain. The undated readouts could fall after 27 December, and declining cash flow erodes the valuation quickly.'),
        'XOM': ('Our $10 cycle-normalized EPS and 18× multiple depend on durable earnings from low-cost production. The smaller weight limits additional energy exposure.',
                'Uaru start-up and the 2027 corporate plan are expected in Q4; both dates remain uncertain.',
                'This is our weakest catalyst on timing. A lower-cycle cash case gives $166.61, close to the $165.87 entry, and DBC already carries energy exposure.'),
        'HPQ': ('We remove the $0.19 tariff-refund benefit from guided GAAP EPS, giving normalized EPS of $2.38. At 13.5×, the earnings value is $32.13.',
                '24 November: results and FY2027 guidance will test cash generation, memory costs and printing demand.',
                'Declining printing demand and PC costs can offset growth. Negative book equity makes cash coverage particularly important.'),
    }

    allocation_rows = []
    stock_rows = []
    positions = []
    valuation_rows = []
    dossier = []
    valuation_data = []
    for i, h in enumerate(holdings):
        ticker = h['ticker']
        actual = h['target_shares'] * h['price'] / nav
        benchmark = analysis['benchmark'][i]
        kind = 'stock' if i >= 6 else 'etf'
        allocation_rows.append(f'''<div class="allocation-row r2-allocation-row {kind}" data-after="{actual * 100}" data-before="{benchmark * 100}"><span>{ticker}</span><div class="allocation-track"><span style="width:{actual * 100:.6f}%"></span></div><strong>{pct(actual)}</strong></div>''')
        positions.append(f'''<tr><th scope="row">{ticker}<span>{html.escape(security_names[ticker])}</span></th><td>{h['target_shares']:,}</td><td>{money(h['price'])}</td><td>{pct(actual)}</td><td>{h['trade_shares']:+,}</td></tr>''')
        if i < 6:
            continue
        p = peers[ticker]
        cash = cash_values[ticker]
        lower = min(p['value'], cash['dcf_value'])
        stock_rows.append(f'''<tr><th scope="row">{ticker}<span>{stock_names[ticker]}</span></th><td>{pct(h['weight'])}</td><td>{pct(p['alpha'])}</td><td>{pct(math.sqrt(p['residual_variance']))}</td></tr>''')
        valuation_rows.append(f'''<div class="r2-value-row" data-ticker="{ticker}"><div><strong>{ticker}</strong><span>Entry {money(h['price'])}</span></div><div class="r2-value-track" aria-hidden="true"><span class="r2-entry-line"></span><span class="r2-value-line" style="width:{(p['value'] / h['price'] - 1) / .5 * 100:.4f}%"></span><i style="left:{(p['value'] / h['price'] - 1) / .5 * 100:.4f}%"></i></div><div class="r2-value-reading"><strong>{money(p['value'])}</strong><span>{pct(p['value'] / h['price'] - 1)} upside</span></div></div>''')
        valuation_data.append({'ticker': ticker, 'price': h['price'], 'earnings': p['value'],
                               'cash': lower, 'full_fcff': cash['dcf_value']})
        thesis, catalyst, risk = cases[ticker]
        eps_display = f"${p['eps']:.3f}" if ticker == 'ADBE' else money(p['eps'])
        dossier.append(f'''<div><dt>{ticker}<span>{stock_names[ticker]} · {pct(h['weight'])} of NAV</span></dt><dd><h3>{eps_display} EPS × {p['pe']:g} = {money(p['value'])}</h3><p>{thesis}</p><p><strong>Catalyst.</strong> {catalyst}</p><details class="formula-details"><summary>Cash-flow check and main risk</summary><p>FCFF value: {money(cash['dcf_value'])}. Lower of earnings and FCFF: {money(lower)}. {risk}</p></details></dd></div>''')

    te_rows = []
    risk_labels = [('Monthly60', '60 monthly returns', 'Required measure'),
                   ('Daily252', '252 daily returns', 'Additional check'),
                   ('Daily63', '63 daily returns', 'Additional check'),
                   ('EWMA252', 'Daily EWMA', 'Additional check')]
    for key, label, role in risk_labels:
        value = analysis['risks'][key]['te']
        te_rows.append(f'''<div class="r2-risk-row"><div><strong>{label}</strong><span>{role}</span></div><div class="r2-risk-track" aria-hidden="true"><span class="r2-budget"></span><i style="left:{value * 1000:.4f}%"></i></div><strong>{pct(value)}</strong></div>''')
    attr_rows = []
    for a in attribution:
        ticker = a['']
        contrib = float(a['Contribution to initial NAV']) * 100
        sign = 'gain' if contrib >= 0 else 'loss'
        attr_rows.append(f'''<div class="r2-attribution-row {sign}"><strong>{ticker}</strong><div class="r2-attribution-track" aria-hidden="true"><span style="width:{abs(contrib) / 2 * 100:.4f}%"></span></div><span>{contrib:+.3f} pp</span></div>''')

    assets = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">'
    header = re.search(r'<header class="site-header">.*?</header>', (DIST / 'round-1.html').read_text()).group()
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Round 2 Research · Meridian Capital</title><meta name="description" content="Meridian Capital's Checkpoint 2: six stocks, valuation cases, catalysts, tracking error and historical tests."><link rel="icon" href="favicon.svg?v=2" type="image/svg+xml">{assets}<link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="round-2.css"><script src="app.js" defer></script><script src="round-2.js" defer></script></head>
<body class="research-page round2-page"><a class="skip" href="#main">Skip to content</a>{header}
<main id="main"><div class="research-back"><a class="text-link" href="index.html#research">← Back to research library</a></div><section class="section allocation-section">
<div class="section-top"><div><p class="eyebrow">Round 2 / Discretionary equity investing</p><h1 class="research-title">Round 2 allocation</h1></div><p class="snapshot-note">Entered 7 November 2026<br>Prices: 6 November close</p></div>
<p class="allocation-intro">We allocate one-third of our post-loss portfolio to six stocks. Their valuations and catalysts guide the selection; their residual risk determines the proportions. The original six-ETF SAA remains our benchmark.</p>
<div class="submission-links" aria-label="Round 2 materials"><a class="text-link" href="{REPORT}">Read final report (PDF) →</a><a class="text-link" href="{MODEL}">Open Excel model ↗</a><a class="text-link" href="{CODE}">Notebooks and data ↗</a></div>
<nav class="research-sections" aria-label="On this page"><span>On this page</span><a href="#allocation" aria-current="location">Allocation</a><a href="#valuations">Stock cases</a><a href="#catalysts">Catalysts</a><a href="#risk">Risk</a><a href="#backtests">Backtests</a><a href="#round1-review">Round 1</a><a href="#implementation">Holdings</a></nav>

<section id="allocation" aria-labelledby="allocation-title"><h2 id="allocation-title" class="r2-section-title">How the portfolio changes</h2>
<div class="r2-funding" aria-label="Target allocation: two-thirds in the original ETFs and one-third in individual stocks"><div><strong>66.67%</strong><span>Original ETFs, scaled proportionally</span></div><div><strong>33.33%</strong><span>Six individual stocks</span></div></div>
<div class="allocation-layout"><div><div class="allocation-toolbar"><h3>Capital allocation</h3><div class="allocation-toggle r2-controls" role="group" aria-label="Allocation comparison"><button type="button" data-r2-allocation="after" aria-pressed="true">Round 2</button><button type="button" data-r2-allocation="before" aria-pressed="false">Original SAA</button></div></div><p class="chart-description" id="r2-allocation-description" aria-live="polite">Whole-share weights at the 6 November close. Stocks are shown in navy.</p><div aria-label="Position weights">{''.join(allocation_rows)}</div><p class="source-note">Every bar uses the same 0–100% scale. Cash is {money(record['cash_usd'])}; its weight is below 0.001%.</p></div>
<div><table class="allocation-table"><caption>Stock targets and the inputs used to size them</caption><thead><tr><th scope="col">Stock</th><th scope="col">NAV weight</th><th scope="col">Annual alpha</th><th scope="col">Residual vol.</th></tr></thead><tbody>{''.join(stock_rows)}</tbody><tfoot><tr><th scope="row">Stocks</th><td>33.33%</td><td colspan="2">One-third target</td></tr></tfoot></table><p class="chart-takeaway">We give more weight to stocks with higher forecast alpha relative to their residual variance. Kroger has the largest weight because its residual risk is relatively low.</p><details class="formula-details"><summary>How we calculate the weights</summary><div class="formula-block"><p>bᵢ = max(αᵢ, 0) / σ²(εᵢ)</p><p>xᵢ = bᵢ / Σbⱼ &nbsp; · &nbsp; wᵢ = xᵢ / 3</p><small>x is a stock's share of the stock basket; w is its share of total NAV. Negative alpha gives zero weight. Risk comes from 60 monthly excess returns regressed on the SAA.</small></div><p class="source-note">The common 50% haircut to valuation-based alpha is an assumption. Annual alpha estimates have considerable uncertainty over the short challenge horizon.</p></details></div></div>
<div class="allocation-reasoning"><h3>Why fund it this way?</h3><div><h4>Keep the SAA as the reference</h4><p>Each ETF target becomes two-thirds of its original weight. This preserves the relative ETF mix while releasing capital for stocks.</p></div><div><h4>Reduce the commodity position</h4><p>DBC falls from 26.95% to 17.97% of NAV. It remains substantial, and Exxon adds further exposure to energy prices.</p></div><div><h4>Use the portfolio's current value</h4><p>The stock budget is {money(record['stock_budget_usd'])}, based on NAV of {money(nav)} after losses and distributions.</p></div></div></section>

<section class="editorial-section" id="valuations" aria-labelledby="valuations-title">{heading('valuations-title', 'The six stock cases', 'We start with normalized earnings and a justified P/E multiple, then check the result against cash flow. Each case needs a catalyst within the challenge horizon.')}
<div class="r2-chart-heading"><h3>Value compared with entry price</h3><div class="allocation-toggle r2-controls" role="group" aria-label="Valuation assumption"><button type="button" data-r2-value="earnings" aria-pressed="true">Earnings case</button><button type="button" data-r2-value="cash" aria-pressed="false">Lower-value check</button></div></div>
<p id="r2-value-description" class="chart-description" aria-live="polite">Earnings-based values used in the original selection. The left marker is each stock's entry price.</p><div class="r2-value-axis" aria-hidden="true"><span>Entry price</span><span>25% higher</span><span>50% higher</span></div><div class="r2-value-chart">{''.join(valuation_rows)}</div>
<p class="source-note">The horizontal scale shows upside from entry price, consistently across stocks. Upside is V/P − 1; margin of safety in the report is 1 − P/V. The lower-value view takes the lower of earnings and FCFF values. The portfolio weights stay fixed in both views.</p>
<dl class="etf-roles r2-stock-cases">{''.join(dossier)}</dl>
<details class="performance-details"><summary>Cash-flow assumptions and stress tests</summary><p>We forecast five years of FCFF and a terminal perpetuity, deduct stock-based compensation as an economic cost, and account for debt, cash and minority interests. Financing-consistent FCFE is a separate calculation check. The Excel model contains growth, rate, funding and price-convergence scenarios.</p><p>Holding weights fixed, forecast residual Information Ratio falls from 0.696 to 0.564 under the lower-value cash checks, and to 0.426 if every original fair value falls by 5%. For Adobe, cash-based annual IRR is 28.17% with full convergence after one year, 17.21% after three years, and 12.43% over three years if the initial discount persists.</p></details></section>

<section class="editorial-section" id="catalysts" aria-labelledby="catalysts-title">{heading('catalysts-title', 'What could change the market’s view?', 'The dates help us judge whether a valuation discount has a chance to close during the challenge.')}
<ol class="r2-timeline"><li><time datetime="2026-11-24">24 November</time><div><h3>HP: results and FY2027 guidance</h3><p>Cash generation, PC margins and printing demand. Confirmed by the issuer.</p></div></li><li class="r2-review-date"><time datetime="2026-11-28">28–29 November</time><div><h3>Next scheduled portfolio rebalance</h3><p>Several catalysts fall after this review. The annual alpha estimates extend beyond our current holding period.</p></div></li><li><time datetime="2026-12-03">3 December</time><div><h3>Kroger and Hormel: earnings and outlooks</h3><p>About 15% of NAV faces company news on the same day. We will watch Kroger's execution and Hormel's recovery and dividend coverage.</p></div></li><li><time datetime="2026-12-09">9 December</time><div><h3>Adobe: results and FY2027 outlook</h3><p>Renewals, pricing and paid AI demand will test the subscription cash-flow case.</p></div></li><li><time datetime="2026-12-12">12–15 December</time><div><h3>Bristol Myers Squibb: ASH data</h3><p>A dated opportunity for pipeline evidence. Other year-end trial readouts have uncertain timing.</p></div></li><li><time datetime="2026-12-27">27 December</time><div><h3>Challenge ends</h3><p>Exxon's Uaru and corporate-plan news, and BMY's undated readouts, could slip beyond this cutoff.</p></div></li></ol>
<p class="chart-takeaway">A scheduled report creates an opportunity for new information. Positive surprises and price convergence remain uncertain. Exxon's undated events give it the weakest timing case.</p></section>

<section class="editorial-section" id="risk" aria-labelledby="risk-title">{heading('risk-title', 'Tracking error across estimation windows', 'The challenge requires annual tracking error of 2–5%, estimated from 60 monthly USD returns. Shorter daily windows give higher estimates.')}
<div class="r2-risk-axis" aria-hidden="true"><span>0%</span><span>2%</span><span>5%</span><span>10%</span></div>{''.join(te_rows)}<p class="source-note">The shaded band is 2–5%. All estimates are annualized. Daily estimates are additional risk checks; the written challenge convention uses monthly returns. Monthly window: November 2021–October 2026.</p>
<table class="backtest-table r2-risk-table"><caption>Ex-ante risk using the same monthly covariance matrix</caption><thead><tr><th scope="col">Measure</th><th scope="col">Original SAA</th><th scope="col">Round 2</th></tr></thead><tbody><tr><th scope="row">Annual tracking error</th><td>0.00%</td><td>3.92%</td></tr><tr><th scope="row">Annual volatility</th><td>7.89%</td><td>9.47%</td></tr><tr><th scope="row">One-month 5% VaR / NAV</th><td>3.74%</td><td>4.50%</td></tr></tbody></table><p class="source-note">VaR assumes normal returns and zero mean: 1.645 × annual volatility / √12. Losses can exceed it. The original 8% volatility target applies to the SAA.</p>
<div class="research-caveat"><h3>What we accepted</h3><p>The monthly estimate fits the prescribed budget. Daily TE estimates of 6.53–7.74% and the historical validation below show substantial uncertainty around near-term risk. Kroger's 8.10% target also slightly exceeds our additional 8% single-stock preference. Both limitations are explicit in the report.</p></div></section>

<section class="editorial-section" id="backtests" aria-labelledby="backtests-title">{heading('backtests-title', 'Testing different starting dates', 'We replay the fixed allocation over 33-session holding periods and compare its returns with the unchanged SAA. DBC changed its methodology on 10 November 2025, so we examine the earlier and later periods separately.')}
<div class="r2-chart-heading"><h3>Historical active return</h3><div class="allocation-toggle r2-controls" role="group" aria-label="DBC methodology period"><button type="button" data-r2-regime="post" aria-pressed="true">After change</button><button type="button" data-r2-regime="pre" aria-pressed="false">Before change</button></div></div>
<p class="chart-description" id="r2-replay-description" aria-live="polite">After the methodology change: {replay['post']['start_first']} to {replay['post']['end_last']}. Zero trading fees.</p>
<div class="allocation-facts r2-replay-stats"><div><span>Mean return above / below SAA</span><strong id="r2-active">{pct(replay['post']['mean_active'], 3)}</strong></div><div><span>Periods outperforming SAA</span><strong id="r2-win">{pct(replay['post']['outperform_rate'], 1)}</strong></div><div><span>Overlapping holding periods</span><strong id="r2-samples">{replay['post']['n_overlapping']}</strong></div></div>
<figure class="r2-interval"><svg id="r2-interval" viewBox="0 0 800 130" role="img" aria-label="95% block-bootstrap confidence interval for mean active return"></svg><figcaption id="r2-interval-caption">95% block-bootstrap interval for mean active return: {pct(replay['post']['active_mean_ci_block'][0])} to {pct(replay['post']['active_mean_ci_block'][1])}.</figcaption></figure>
<p class="chart-takeaway" id="r2-independent">The 217 overlapping periods contain only 6–7 non-overlapping windows per starting offset. The interval includes zero, and the later-period mean is below the SAA.</p>
<details class="performance-details"><summary>How to interpret these tests</summary><p>We use today's selected stocks and assumptions throughout the history. Selection bias and repeated use of these data limit what the replay says about future returns. The many overlapping windows share observations. A block bootstrap allows for dependence when estimating the interval for mean active return.</p><p>At ten monthly historical forecast dates where monthly TE was within budget, realized 33-session daily TE subsequently exceeded 5% in 80% of cases. These dates also overlap. This result reinforces the uncertainty shown by our current daily risk estimates.</p><p><a class="text-link" href="{CODE}/round2_analysis.ipynb">Read the test methodology and comparisons in the notebook ↗</a></p></details>
<div class="r2-ir-note"><h3>How the forecast IR fits in</h3><p>The stock basket has forecast residual IR of 0.696, including residual correlations. The classroom independence approximation gives 0.756. These estimates depend on our valuations and alpha haircut. The historical replay provides weak support for near-term outperformance, so we treat the forecast IR cautiously.</p></div></section>

<section class="editorial-section" id="round1-review" aria-labelledby="round1-title">{heading('round1-title', 'What happened in Round 1', 'From the 16 October close to 6 November, NAV fell from $100 million to $97,115,068.58, a return of −2.885%. Annualized realized volatility was 8.14% and Sharpe was −6.50 across 15 daily returns.')}
<div class="r2-round1-layout"><div><h3>Contribution to the total return</h3><div class="r2-attribution">{''.join(attr_rows)}</div><p class="source-note">Percentage points of initial NAV, including entitled distributions. All bar lengths use the same scale; labels give the sign.</p></div><div><h3>DBC accounted for about 61% of the net loss</h3><p>DBC contributed −1.757 percentage points and SPY a further −0.955 points. SCHD, VGSH and STIP partly offset those losses. This experience supports reducing commodity exposure, although DBC remains a large holding.</p><details class="formula-details"><summary>NAV reconciliation</summary><p>Securities: $97,014,139.67<br>Opening cash: $12.12<br>VGSH distribution: $16,372.15<br>STIP distribution: $84,544.63<br><strong>Total NAV: $97,115,068.58</strong></p><p>Distributions are recognized on the ex-date and counted once. The report gives payment dates and per-share amounts.</p></details><p class="source-note">Performance is calculated from public daily prices and distributions. The short sample makes annualized Sharpe highly sensitive to individual losses.</p></div></div></section>

<section class="editorial-section" id="implementation" aria-labelledby="implementation-title">{heading('implementation-title', 'The complete portfolio', 'Recorded Bloomberg entry date: 7 November 2026. Prices are the 6 November USD close. Whole-share quantities include the extra SPY and Adobe shares.')}
<div class="backtest-scroll" role="region" aria-label="Complete Round 2 holdings and trades" tabindex="0"><table class="allocation-table r2-holdings"><caption>All identifiers use the format “ticker US Equity”; all positions and trades are in USD. Positive trades are purchases; negative trades are sales.</caption><thead><tr><th scope="col">Security</th><th scope="col">Shares</th><th scope="col">Price</th><th scope="col">NAV weight</th><th scope="col">Trade shares</th></tr></thead><tbody>{''.join(positions)}</tbody><tfoot><tr><th scope="row">Cash</th><td colspan="2">$116.05</td><td>0.00012%</td><td>Zero fees</td></tr></tfoot></table></div><p class="source-note">Securities: $97,114,952.53. Stocks: $32,371,559.04, or 33.33320% of NAV. Whole-share rounding leaves stocks $130.49 below the exact one-third budget.</p><a class="text-link" href="data/round2-holdings.csv" download>Download quantities and trades (CSV)</a> &nbsp; <a class="text-link" href="materials/round-2-portfolio-description.pdf">Portfolio description (PDF) →</a></section>

<section class="editorial-section" id="methodology" aria-labelledby="methodology-title">{heading('methodology-title', 'From research to the recorded allocation', 'The report and notebooks document the assumptions and calculations behind this page. Stock weights and quantities remain unchanged throughout the later valuation checks.')}
<ol class="r2-method"><li><h3>Value the companies</h3><p>Choose normalized EPS and a P/E multiple, then examine financial quality, capital allocation, cash flow and catalyst timing.</p></li><li><h3>Translate the cases into alpha inputs</h3><p>Apply a common 50% haircut to annual full-convergence valuation premia. This is a judgment about uncertainty; the short challenge horizon calls for caution.</p></li><li><h3>Size and fund the basket</h3><p>Use alpha divided by residual variance, allocate one-third of NAV to stocks and scale the ETF targets proportionally. Compare all 420 three-to-six-stock combinations from nine researched names.</p></li><li><h3>Check the allocation and enter whole shares</h3><p>Test monthly and daily risk, staggered holding periods, cash assumptions and slower convergence. Use reconciled post-loss NAV and zero fees for the implementation quantities.</p></li></ol>
<div class="publication-note"><div><h3>Research record</h3><p>Prices at 6 November 2026<br>Report revised 8 November 2026</p></div><div><p>The latest team report uses the same NAV and quantities as this page. Read the full valuation dossiers and source references, or reproduce the calculations from the saved inputs.</p><p><a class="text-link" href="{REPORT}">Final report (PDF) →</a> &nbsp; <a class="text-link" href="{MODEL}">Excel model ↗</a> &nbsp; <a class="text-link" href="{CODE}">Notebooks and data ↗</a></p><p class="source-note">The team's presentation is being finalized separately.</p></div></div></section>
</section></main><footer><div><a class="wordmark" href="index.html#main">MERIDIAN<span>CAPITAL</span></a><p>Asset Management Challenge 2026<br>Academic simulation · Not an investment offering</p></div><div class="footer-links"><a href="round-1.html">Round 1 research</a><a href="{CODE}">Round 2 code &amp; data ↗</a><a href="#main">Back to top</a></div></footer>
<script type="application/json" id="round2-data">{json.dumps({'valuations': valuation_data, 'replay': {k: {q: v[q] for q in ['start_first', 'end_last', 'n_overlapping', 'nonoverlap_n_min', 'nonoverlap_n_max', 'mean_active', 'outperform_rate', 'active_mean_ci_block']} for k, v in replay.items()}})}</script></body></html>'''
    (DIST / 'round-2.html').write_text(page)
    shutil.copy2(report_path, DIST / REPORT)
    shutil.copy2(RESEARCH / 'results/valuation/entered_holdings.csv', DIST / 'data/round2-holdings.csv')
    report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()
    (DIST / 'data/round2-publication.json').write_text(json.dumps({
        'status': 'Published', 'price_date': record['price_date'],
        'entry_date': record['bloomberg_entry_date'], 'nav_usd': nav,
        'report': REPORT, 'report_sha256': report_sha, 'report_revision': '2026-11-08',
        'stock_tickers': analysis['stocks'], 'source': CODE}, indent=2) + '\n')
    print(f'Built Round 2 page; report SHA-256 {report_sha}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    build(args.report.resolve())
