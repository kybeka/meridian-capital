"""Financing-consistent valuation and an explicitly conditional portfolio decision.

All money is USD millions except prices and dividends per share. Inputs stop on
6 November 2026. Forecasts are analyst scenarios, never issuer guidance.
"""
from pathlib import Path
from itertools import combinations
import json
import numpy as np
import pandas as pd
from scipy.optimize import brentq, minimize
from portfolio_inputs import ROOT, ETFS, SAA, POLICY, quotes, statements, ttm, data, rows, covariance_set

STOCKS = ['ADBE', 'KR', 'HRL', 'BMY', 'XOM', 'HPQ', 'FDS', 'INTU', 'GILD']
OUT = ROOT / 'results/valuation'
OUT.mkdir(exist_ok=True)

SOURCES = {
 'ADBE':'https://www.sec.gov/Archives/edgar/data/796343/000079634326000147/adbeex991q326.htm',
 'KR':'https://ir.kroger.com/news/news-details/2026/Kroger-Reports-Second-Quarter-2026-Results-and-Updates-Guidance-for-2026/default.aspx',
 'HRL':'https://www.hormelfoods.com/wp-content/uploads/Hormel-Earnings-Release-Q3-2026_FINAL.pdf',
 'BMY':'https://www.bms.com/assets/bms/us/en-us/pdf/investor-info/doc_financials/quarterly_reports/2026/BMY-Q3-2026-Earnings-Press-Release-0039.pdf',
 'XOM':'https://investor.exxonmobil.com/sec-filings/all-sec-filings/content/0002115436-26-000020/xom-20260930.htm',
 'HPQ':'https://www.hp.com/content/dam/sites/garage-press/press/press-releases/2026/q3-fy26-earnings/HP_Inc_Reports_Q3FY26_Earnings.pdf',
 'FDS':'https://investor.factset.com/static-files/ba920b54-c271-426a-84e9-fd1208cfee67',
 'INTU':'https://investors.intuit.com/sec-filings/all-sec-filings/content/0000896878-26-000029/fy26q4earningspressrelease.htm',
 'GILD':'https://www.sec.gov/Archives/edgar/data/882095/000088209526000039/gild-20260930.htm',
}

RATIONALE = {
 'ADBE': '8% cash growth is below latest 13% revenue growth. SBC remains an economic expense. Competitive pressure from AI and REA/Artcraft is tested through lower cash and growth, rather than asserted customer losses. December 9 earnings are after the next rebalance.',
 'KR': '3% cash growth assumes modest sales, mix and efficiency progress, not a repeat of buyback-driven EPS growth. Correct debt is 16,997, excluding 7,161 of operating leases already expensed in CFO. Thin margins and its 2.3-2.5x net-debt/EBITDA target make financing important. December 3 earnings are after the next rebalance.',
 'HRL': '2% cash growth follows the low end of organic sales guidance, with no speculative acquisition earnings. Brakebush is 1,055 and expected to close in FY27 Q1. Base deal NPV is zero: acquired assets equal consideration, not a free asset or a deduction of the purchase price twice. Financing and value destruction are separate stresses. December 3 outlook is after the next rebalance.',
 'BMY': 'Preserve the original flat-cash base assumption: pipeline delivery and cost savings offset legacy erosion in aggregate. This is an analyst scenario, not company guidance. Test 1%, 2% and 5% annual cash declines separately, rather than quietly replace the base case. The Q3 release reports Growth Portfolio revenue growth of 12%, but that does not prove future patent losses will be offset. Remaining-2026 readouts are uncertain and binary.',
 'XOM': 'Keep business conditions consistent with the original normalized EPS scenario of 10: normalized common earnings are EPS times current shares; add the median 2023-2025 CFO-minus-common-net-income bridge of 21,342 to estimate normalized consolidated CFO. This bridge includes D&A, working capital, taxes and minority effects; it is not all depreciation. Retain TTM PP&E spending and charge 1,040 of annualized 9M stock awards. Subtract 6,731 NCI at book value as a market-value proxy. A lower-cycle historical-CFO case is a separate stress, not an unexplained base change.',
 'HPQ': 'Use guided 3,100 FCF less 176.13 tariff-refund cash proxy and 479 SBC. 4% initial growth and 3% terminal growth need PC cash conversion and printing stabilization. The guide is levered FCF, so interest is unlevered once. November 24 earnings are a timely test.',
 'FDS': 'Alternative reviewed: 5.5% first-stage cash growth is aligned with FY27 5-6.5% ASV guidance; 3% terminal growth assumes mature nominal growth. Do not use the old 7% cash growth. Fiscal 2026 CFO, capex, SBC and debt are verified to the release. November 10 Investor Day is timely. AI pricing competition and compensation accrual reversal remain risks.',
 'INTU': 'Alternative reviewed: remove 1,279 of FY26 deferred-tax addback from recurring CFO as a conservative no-repeat scenario. This is a normalization assumption, not a claim that past cash was fictitious. Keep SBC charged, remove operating leases from debt, and show an unadjusted-tax alternative. November 19 earnings are timely, but the cash margin is insufficient in the normalized case.',
 'GILD': 'Alternative reviewed: revert CFO to FY2025 10,019 rather than extrapolate TTM 14,479, while retaining current capex and SBC. Acquisition cash is already reflected in cash/debt; it is not added back or charged twice. No future deal benefit is forecast. 4% cash growth and 2.5% terminal growth require continued product delivery. December ASH/FDA events are binary and do not receive assumed approval probabilities.',
}

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, allow_nan=False))

def prepare_inputs():
    p, d, m, ex = data(STOCKS)
    old = {r['ticker']: r for r in rows(STOCKS, m, ex)}
    result = []
    debts = {'ADBE':6363., 'KR':16997., 'HRL':2855.123, 'BMY':42877.,
             'XOM':34250., 'HPQ':9160., 'FDS':1370.022, 'INTU':7669., 'GILD':26231.}
    for t in STOCKS:
        r = old[t]
        q, annual, cashflow = statements(t, 'quarterly'), statements(t), ttm(t)
        cash = float(q.CashCashEquivalentsAndShortTermInvestments.iloc[-1] / 1e6)
        if t == 'KR': cash = 1475.
        if t == 'BMY': cash = 12959.
        cfo = cashflow['OperatingCashFlow'] / 1e6
        capex = abs(cashflow['CapitalExpenditure']) / 1e6
        sbc = cashflow['StockBasedCompensation'] / 1e6 if cashflow['StockBasedCompensation'] is not None else 1040.
        adjustment = 0.
        if t == 'XOM':
            history=annual.iloc[-3:]
            bridge=float((history.OperatingCashFlow-history.NetIncome).median()/1e6)
            normalized_cfo=r['eps']*quotes()[t]['sharesOutstanding']/1e6+bridge
            adjustment=cfo-normalized_cfo
        if t == 'HPQ': adjustment = (cfo-capex) - (3100.-176.13)
        if t == 'INTU': adjustment = 1279.
        if t == 'GILD': adjustment = cfo - 10019.
        interest = float(q.InterestExpense.tail(4).sum()/1e6)
        # Cash income is removed before adding cash separately. Releases with a
        # separately verified net interest figure take precedence over the proxy.
        interest_income = cash * POLICY['rf10y']
        net_interest = interest - interest_income
        interest_basis = 'TTM provider interest less 4.84% yield on latest cash; explicit cash-income proxy.'
        if t == 'KR':
            net_interest = 661.
            interest_basis = 'Issuer rolling-four-quarter net interest, Table 5.'
        if t == 'FDS':
            net_interest = 54.684 - 4.064
            interest_basis = 'Issuer FY26 interest expense 54.684 less interest income 4.064.'
        if t == 'HRL':
            net_interest = interest - 19.667*4/3
            interest_basis = 'TTM interest less annualized issuer nine-month interest income 19.667.'
        tau = .24 if t in ['KR', 'HRL'] else .21
        growth = r['cash_growth']
        terminal = r['terminal_growth']
        if t == 'BMY': growth, terminal = 0., 0.
        if t == 'FDS': growth = .055
        shares = quotes()[t]['sharesOutstanding']/1e6
        spread = .005 if t in ['ADBE', 'XOM'] else .015 if t == 'HPQ' else .01
        dividends = float(quotes()[t].get('dividendRate', 0.) or 0.)
        result.append(dict(ticker=t, price=r['price'], shares=shares,
             cfo=cfo, capex=capex, sbc=sbc, normalization=adjustment,
             net_interest=net_interest, tax=tau, cash=cash, debt=debts[t],
             minority=6731. if t=='XOM' else 0., debt_rate=POLICY['rf10y']+spread,
             k=r['k'], beta_market=r['beta_market'], beta_saa=r['beta_saa'],
             residual_variance=r['residual_variance'], growth=growth, terminal_growth=terminal,
             years=5, dividend=dividends, dividend_growth=min(max(growth,0.),.02),
             eps=r['eps'], pe=r['pe'], multiple_value=r['value'],
             source=SOURCES[t], interest_basis=interest_basis, rationale=RATIONALE[t],
             statement_period={'ADBE':'2026-08-28','KR':'2026-08-15','HRL':'2026-07-26'}.get(t,str(q.index[-1])),
             provider_period=str(q.index[-1]),
             source_note='Flow totals are four quarters from archived statements, except explicit normalization. Balances are latest observations; shares are the archived November 6 outstanding count, not diluted EPS shares. Debt/cash are corrected to issuer tables. Debt rates and taxes are forecast assumptions, not bond quotes or reported tax rates.'))
    return result, (p,d,m,ex)

def discount_rates(a, k_shift=0., debt_rate_shift=0.):
    market_equity = a['price']*a['shares']
    cash = a['cash']
    operating_equity = market_equity-cash
    k = a['k']+k_shift
    ke_op = (k*market_equity-POLICY['rf10y']*cash)/operating_equity
    # Noncontrolling interests are equity capital, priced at the same operating
    # equity hurdle in the absence of a quoted minority market capitalization.
    equity_capital = operating_equity+a['minority']
    leverage = a['debt']/(equity_capital+a['debt'])
    kd = a['debt_rate']+debt_rate_shift
    wacc = ke_op*(1-leverage)+kd*(1-a['tax'])*leverage
    return dict(k=k, ke_op=ke_op, kd=kd, leverage=leverage, wacc=wacc)

def fcff_value(a, growth=None, years=None, terminal=None, cash_scale=1., k_shift=0., debt_rate_shift=0., value_loss=0.):
    rates = discount_rates(a,k_shift,debt_rate_shift)
    g = a['growth'] if growth is None else growth
    h = a['years'] if years is None else years
    gt = a['terminal_growth'] if terminal is None else terminal
    f0 = (a['cfo']-a['normalization']-a['capex']-a['sbc']+a['net_interest']*(1-a['tax']))*cash_scale
    if rates['wacc'] <= gt: raise ValueError('Terminal growth must be below WACC')
    flows = [f0*(1+g)**j for j in range(1,int(np.floor(h))+1)]
    # Fractional duration is a smooth two-stage extension, used only to solve
    # implied duration. Integer forecast schedules remain the operating model.
    if int(h)==h:
        pv = sum(f/(1+rates['wacc'])**j for j,f in enumerate(flows,1))
    else:
        z=(1+g)/(1+rates['wacc'])
        pv=f0*z*(1-z**h)/(1-z) if abs(z-1)>1e-12 else f0*h
    terminal_value=f0*(1+g)**h*(1+gt)/(rates['wacc']-gt)
    ev=pv+terminal_value/(1+rates['wacc'])**h
    equity=ev-a['debt']+a['cash']-a['minority']-value_loss
    return dict(**rates, fcff0=f0, ev=ev, equity=equity, value=equity/a['shares'],
                pv_terminal=terminal_value/(1+rates['wacc'])**h,
                terminal_share=(terminal_value/(1+rates['wacc'])**h)/ev,
                terminal_value=terminal_value, growth=g, terminal_growth=gt, years=h)

def solve_root(fn, lo, hi):
    if fn(lo)*fn(hi)>0: return None
    return float(brentq(fn,lo,hi,xtol=1e-12))

def finance_schedule(a, model, n=10):
    """FCFE/FCFF identity under one constant market-value debt policy.

    The initial difference between target model debt and reported debt is kept
    in cash. It is disclosed as a modeling recapitalization, not a company plan.
    Future non-dividend FCFE is retained at an after-tax risk-free cash yield.
    """
    f0, g, gt, wacc, d, kd, ke = [model[k] for k in ['fcff0','growth','terminal_growth','wacc','leverage','kd','ke_op']]
    h=int(model['years'])
    f=lambda t: f0*(1+g)**min(t,h)*(1+gt)**max(t-h,0)
    firm=[0.]*(n+1)
    firm[n]=f(n+1)/(wacc-gt)
    for j in range(n-1,-1,-1): firm[j]=(f(j+1)+firm[j+1])/(1+wacc)
    debt=np.array(firm)*d
    # Consolidated equity includes NCI; subtract its proxy at date 0 and treat
    # its future claim as proportional to consolidated equity in return paths.
    common_ratio=(model['ev']*(1-d)-a['minority'])/(model['ev']*(1-d))
    initial_cash=a['cash']+debt[0]-a['debt']
    cash=initial_cash
    output=[]
    for j in range(1,n+1):
        interest=kd*debt[j-1]
        borrowing=debt[j]-debt[j-1]
        fcfe=f(j)-interest*(1-a['tax'])+borrowing
        common_fcfe=fcfe*common_ratio
        dividend=a['dividend']*a['shares']*(1+a['dividend_growth'])**j
        cash=cash*(1+POLICY['rf10y']*(1-a['tax']))+common_fcfe-dividend
        fair_price=((1-d)*firm[j]*common_ratio+cash)/a['shares']
        output.append(dict(ticker=a['ticker'],year=j,fcff=f(j),firm_end=firm[j],
            debt_begin=debt[j-1],interest=interest,net_borrowing=borrowing,debt_end=debt[j],
            fcfe=fcfe,equity_end=(1-d)*firm[j],dividend=dividend/a['shares'],
            retained_cash=cash,fair_price=fair_price,common_fcfe=common_fcfe,
            equity_rate=ke,initial_cash=initial_cash,minority_ratio=common_ratio))
    pv=sum(r['fcfe']/(1+ke)**r['year'] for r in output[:h])+output[h-1]['equity_end']/(1+ke)**h
    equity_from_fcfe=pv+(debt[0]-a['debt'])+a['cash']-a['minority']
    np.testing.assert_allclose(equity_from_fcfe,model['equity'],rtol=1e-10)
    return output, float(equity_from_fcfe/a['shares'])

def irr(cashflows):
    return solve_root(lambda r:sum(v/(1+r)**j for j,v in enumerate(cashflows)), -.95, 10.)

def value_stocks(inputs):
    valuations=[];schedules=[];convergence=[];sensitivities=[]
    for a in inputs:
        base=fcff_value(a)
        decision=min(base['value'],a['multiple_value'])
        # Reconcile two independent methods conservatively. The haircut reduces
        # cash flows; it never changes sourced observations or raises a value.
        required_ev=decision*a['shares']+a['debt']-a['cash']+a['minority']
        haircut=required_ev/base['ev']
        adopted=fcff_value(a,cash_scale=haircut)
        schedule,fcfe_check=finance_schedule(a,adopted)
        schedules.extend(schedule)
        implied_g=solve_root(lambda g:fcff_value(a,growth=g,cash_scale=haircut)['value']-a['price'],-.5,.5)
        implied_h=None if abs(a['growth']-a['terminal_growth'])<1e-12 else solve_root(lambda h:fcff_value(a,years=h,cash_scale=haircut)['value']-a['price'],0.,50.)
        duration_note=('Not identifiable: first and terminal growth are equal.' if abs(a['growth']-a['terminal_growth'])<1e-12
            else 'No duration solution between 0 and 50 years under the fixed cash/growth assumptions.' if implied_h is None
            else 'Years of the first-stage growth or decline, holding the other assumptions fixed.')
        decision_alpha=.5*(1+a['k'])*(decision/a['price']-1)
        rec=dict(**a,**{f'dcf_{k}':v for k,v in base.items()}, decision_value=decision,
             cash_haircut=haircut,alpha=decision_alpha,alpha_full=decision_alpha*2,
             gap=decision/a['price']-1,implied_growth=implied_g,
             implied_duration=implied_h,implied_duration_note=duration_note,fcfe_value=fcfe_check,
             adopted_fcff0=adopted['fcff0'],adopted_ev=adopted['ev'],
             break_even_cash_scale=(a['price']*a['shares']+a['debt']-a['cash']+a['minority'])/adopted['ev'],
             forecast_fcff_to_cfo=adopted['fcff0']/a['cfo'],positive_alpha=bool(decision_alpha>0))
        valuations.append(rec)
        for h in [1,3,5,10]:
            dividends=[r['dividend'] for r in schedule[:h]]
            target=schedule[h-1]['fair_price']
            full=irr([-a['price'],*dividends[:-1],dividends[-1]+target])
            discount=a['price']/decision
            never=irr([-a['price'],*dividends[:-1],dividends[-1]+target*discount])
            fair=irr([-decision,*dividends[:-1],dividends[-1]+target])
            convergence.append(dict(ticker=a['ticker'],years=h,full_convergence_irr=full,
                no_convergence_irr=never,initial_k=a['k'],full_minus_k=full-a['k'],
                never_minus_k=never-a['k'],fair_purchase_irr=fair,
                valuation_return_premium=full-fair,terminal_fair_price=target,
                dividends_paid=sum(dividends),min_retained_cash=min(r['retained_cash']for r in schedule[:h]),
                basis='Annual dividends with no buybacks; residual FCFE retained in cash at after-tax Treasury yield. Full closure occurs only at the specified sale year. Never case preserves the initial proportional discount on each terminal fair price.'))
        for label,kwargs in [('Base',{}),('Cash minus 10%',{'cash_scale':.9}),
             ('Cash minus 20%',{'cash_scale':.8}),('Cost equity plus 1pp',{'k_shift':.01}),
             ('Cost equity plus 2pp',{'k_shift':.02}),('Debt cost plus 2pp',{'debt_rate_shift':.02}),
             ('Zero growth',{'growth':0.,'terminal':0.}),
             ('Terminal growth minus 1pp',{'terminal':a['terminal_growth']-.01})]:
            v=fcff_value(a,**kwargs)['value']
            sensitivities.append(dict(ticker=a['ticker'],scenario=label,dcf_value=v,
                 decision_value=min(v,a['multiple_value']),gap=min(v,a['multiple_value'])/a['price']-1))
        if a['ticker']=='HRL':
            for loss in [.25,.5,1.]:
                v=fcff_value(a,value_loss=1055*loss)['value']
                sensitivities.append(dict(ticker='HRL',scenario=f'Brakebush {loss:.0%} consideration destroyed',dcf_value=v,decision_value=min(v,a['multiple_value']),gap=min(v,a['multiple_value'])/a['price']-1))
        if a['ticker']=='BMY':
            for decline in [.01,.02,.05]:
                v=fcff_value(a,growth=-decline,terminal=0.)['value']
                sensitivities.append(dict(ticker='BMY',scenario=f'Patent erosion: cash declines {decline:.0%} for 5 years',dcf_value=v,decision_value=min(v,a['multiple_value']),gap=min(v,a['multiple_value'])/a['price']-1))
        if a['ticker']=='XOM':
            b=dict(a,normalization=a['cfo']-float(statements('XOM').OperatingCashFlow.iloc[-3:].median()/1e6))
            v=fcff_value(b)['value']
            sensitivities.append(dict(ticker='XOM',scenario='Lower-cycle median historical CFO',dcf_value=v,decision_value=min(v,a['multiple_value']),gap=min(v,a['multiple_value'])/a['price']-1))
        if a['ticker']=='INTU':
            b=dict(a,normalization=0.)
            v=fcff_value(b)['value']
            sensitivities.append(dict(ticker='INTU',scenario='Repeat FY26 deferred-tax cash benefit',dcf_value=v,decision_value=min(v,a['multiple_value']),gap=min(v,a['multiple_value'])/a['price']-1))
    return valuations,schedules,convergence,sensitivities

def portfolio_research(valuations, market):
    """Audit the recorded portfolio at fixed weights; never generate new holdings."""
    p,d,m,ex=market
    names=ETFS+STOCKS
    cov=covariance_set(d,m)
    benchmark=np.r_[SAA,np.zeros(len(STOCKS))]
    alpha=np.array([r['alpha']for r in valuations])
    sx=ex[ETFS].tail(60).to_numpy()@SAA
    residual=np.column_stack([ex[t].tail(60).to_numpy()-ex[t].tail(60).mean()-valuations[i]['beta_saa']*(sx-sx.mean())for i,t in enumerate(STOCKS)])
    rc=np.cov(residual,rowvar=False,ddof=1)*12
    old=json.loads((ROOT/'results/implementation.json').read_text())
    original=json.loads((ROOT/'results/analysis.json').read_text())
    nav=old['nav']
    target=np.r_[original['etf_weights'],[original['stock_weights'][original['stocks'].index(t)]if t in original['stocks']else 0 for t in STOCKS]]
    entered=np.zeros(len(names))
    for h in old['holdings']:entered[names.index(h['ticker'])]=h['target_shares']*h['price']/nav
    def metrics(w,label):
        z=w-benchmark;sw=w[6:];sig=np.sqrt(sw@rc@sw);av=sw@alpha
        return dict(name=label,stocks=[t for i,t in enumerate(STOCKS)if sw[i]>1e-10],weights=w.tolist(),
            audit_alpha_nav=float(av),audit_full_residual_ir=float(av/sig)if sig>0 else 0.,
            max_stock=float(sw.max()),risk={k:float(np.sqrt(z@c@z))for k,c in cov.items()},
            total_vol={k:float(np.sqrt(w@c@w))for k,c in cov.items()})
    chosen=metrics(target,'Recorded portfolio target')
    comparisons=[chosen,metrics(entered,'Entered holdings'),metrics(benchmark,'Unchanged SAA')]
    control=np.r_[SAA*2/3,np.zeros(len(STOCKS))];control[0]+=1/3
    comparisons.append(metrics(control,'One-third SPY control'))
    holdings=[]
    for h in old['holdings']:
        holdings.append(dict(**h,entered_value=h['target_shares']*h['price'],
                             entered_weight=h['target_shares']*h['price']/nav))
    return dict(chosen=chosen,comparisons=comparisons,implementation=holdings,
        nav=nav,stock_budget=nav/3,entered_cash=old['remaining_cash_after_cost'],
        entered_stock_fraction=float(entered[6:].sum()),old_implementation=old,
        original_model_ir=original['ir'],original_rows=original['rows'],
        names=names,covariances={k:c.tolist()for k,c in cov.items()},residual_covariance=rc.tolist(),
        status='Fixed-holdings valuation audit. Original weights, entered quantities and no-fee cash are unchanged. Audit cash-value alphas are sensitivity results and do not trigger reweighting.',
        construction='The recorded weights were constructed from the original normalized-EPS/P-E alphas and residual variances. New cash cases assess that thesis at fixed weights. No revised target, trade list or candidate share quantities are issued.'),market

def run():
    inputs,market=prepare_inputs()
    valuations,schedules,convergence,sensitivities=value_stocks(inputs)
    research,_=portfolio_research(valuations,market)
    funding=[]
    for a in inputs:
        if a['ticker'] not in ['HRL','KR']:continue
        flow=ttm(a['ticker']);v=next(r for r in valuations if r['ticker']==a['ticker'])
        dividend=a['dividend']*a['shares']
        coupons=float(statements(a['ticker'],'quarterly').InterestExpense.tail(4).sum()/1e6)
        cash_income_before_tax=coupons-a['net_interest']
        if a['ticker']=='KR':
            # The issuer figure is already net interest. Do not add an assumed
            # cash yield a second time in the unchanged-financing case.
            coupons=a['net_interest']
            cash_income_before_tax=0.
        for label,new_debt,rate in [('Existing coupons, no extra borrowing',0.,coupons/a['debt']),
             ('Refinance debt at model borrowing cost',0.,a['debt_rate'])]+([
             ('Brakebush fully debt funded, existing coupons',1055.,None),
             ('Brakebush debt funded plus full refinancing',1055.,a['debt_rate'])] if a['ticker']=='HRL' else []):
            interest=coupons+new_debt*a['debt_rate'] if rate is None else rate*(a['debt']+new_debt)
            cash_income=cash_income_before_tax*(1-a['tax'])
            fcfe=v['dcf_fcff0']-interest*(1-a['tax'])+cash_income
            buybacks=abs(flow['RepurchaseOfCapitalStock'] or 0)/1e6
            funding.append(dict(ticker=a['ticker'],scenario=label,debt=a['debt']+new_debt,
                fcfe_no_net_borrowing=fcfe,annual_dividends=dividend,dividend_cover=fcfe/dividend,
                annualized_or_ttm_buybacks=buybacks,after_dividend_cash=fcfe-dividend,
                note='Funding stress only. Cash investment income is held at the source/proxy used in the CFO bridge. No acquired operating benefit, extra borrowing, dividend cut or future buybacks assumed. Full refinancing at the model rate is not a coupon forecast.'))
    save('inputs.json',inputs);save('valuations.json',valuations);save('schedules.json',schedules);save('funding_checks.json',funding)
    save('convergence.json',convergence);save('sensitivities.json',sensitivities);save('portfolio.json',research)
    for n,x in [('valuations',valuations),('schedules',schedules),('convergence',convergence),('sensitivities',sensitivities),('entered_holdings',research['implementation'])]:pd.DataFrame(x).to_csv(OUT/(n+'.csv'),index=False)
    p,d,m,ex=market;p.to_csv(OUT/'adjusted_prices.csv');d.to_csv(OUT/'daily_returns.csv');m.to_csv(OUT/'monthly_returns.csv');ex.to_csv(OUT/'monthly_excess.csv')
    print(pd.DataFrame(valuations)[['ticker','price','dcf_value','decision_value','alpha','implied_growth']].round(4).to_string(index=False))
    print(json.dumps({k:v for k,v in research['chosen'].items()if k!='weights'},indent=2))
    return inputs,valuations,schedules,convergence,sensitivities,research,market

if __name__=='__main__':run()
