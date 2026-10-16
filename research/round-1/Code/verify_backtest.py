"""Rebuild source returns, initial fit checks, and a dollar-accounting backtest."""
from pathlib import Path
import json
import numpy as np,pandas as pd
P=Path(__file__).resolve().parents[1]
A=['SPY','EEMV','DBC','VGSH','SCHD','STIP']
s=json.loads((P/'Results/backtest_results.json').read_text())
prices=pd.read_csv(P/'Data/month_end_prices.csv',index_col=0,parse_dates=True)[A]
r=prices/prices.shift(1)-1;r=r.dropna()
recorded=pd.read_csv(P/'Data/monthly_returns.csv',index_col=0,parse_dates=True)[A]
assert np.max(abs(r.values-recorded.values))<1e-12
rf=pd.read_csv(P/'Data/risk_free_monthly.csv',index_col=0,parse_dates=True).monthly_rf_proxy
raw=pd.read_csv(P/'Data/Raw sources/FRED_DGS1MO.csv',parse_dates=['observation_date'])
raw['DGS1MO']=pd.to_numeric(raw['DGS1MO'],errors='coerce');raw=raw.dropna().set_index('observation_date').sort_index()
for day,value in rf.loc['2011-11':'2026-09'].items():
 prior=raw.loc[raw.index<day.replace(day=1),'DGS1MO'].iloc[-1]
 assert abs(prior/100*day.days_in_month/365-value)<1e-12
checks=0;largest=0
for key,path in [('fixed_proposal_retrospective','fixed_proposal_monthly_returns.csv'),('historical_fit_2016','historical_fit_2016_monthly_returns.csv'),('historical_fit_2021','historical_fit_2021_monthly_returns.csv')]:
 group=s[key] if key=='fixed_proposal_retrospective' else s[key]['strategies'];out=pd.read_csv(P/'Results'/path,index_col=0,parse_dates=True)
 for name,z in group.items():
  w=np.array([z['weights'][a] for a in A]);assert abs(w.sum()-1)<1e-10 and min(w)>=-1e-10
  holdings=np.zeros(6);nav=1e8;hist=[];rv=[]
  for day in out.index:
   before=nav;traded=np.sum(np.abs(nav*w-holdings));fee=.001*traded
   holdings=(nav-fee)*w*(1+r.loc[day].values);nav=holdings.sum();rv.append(nav/before-1);hist.append(nav)
  x=pd.Series(rv,index=out.index);gap=np.max(abs(x-out[name]));assert gap<1e-12;largest=max(largest,gap)
  wealth=np.r_[1e8,hist];vol=x.std(ddof=1)*np.sqrt(12)
  q={'cagr':(nav/1e8)**(12/len(x))-1,'volatility':vol,'sharpe':(x-rf.reindex(x.index)).mean()*12/vol,'max_month_end_drawdown':min(wealth/np.maximum.accumulate(wealth)-1),'historical_one_month_95pct_var':-np.percentile(x,5),'terminal_value_usd':nav}
  for metric,value in q.items():assert abs(value-z['statistics'][metric])<max(1e-10,abs(value)*1e-11),(key,name,metric)
  checks+=len(x)
 if key!='fixed_proposal_retrospective':
  t=s[key]['training'];h=r.loc[t['fit_first']:t['fit_last']];assert len(h)==60 and h.index[-1]<out.index[0]
  cv=np.cov(h.values,rowvar=False,ddof=1)*12;w=np.array([t['weights'][a] for a in A]);risk=w*(cv@w)/(w@cv@w)
  assert abs(np.sqrt(w@cv@w)-.08)<1e-7 and w.max()<=.35+1e-7 and max(risk)<=.4+1e-7 and risk[[0,1,4]].sum()<=.65+1e-7
  assert w[[0,4]].sum()>=.05-1e-7 and min(w[1],w[2],w[3],w[5])>=.05-1e-7 and w[[3,5]].sum()>=.20-1e-7
  assert max(t['seed_objectives'])-min(t['seed_objectives'])<1e-6
for name in ['Fixed equal weight','Fixed risk parity']:
 z=s['fixed_proposal_retrospective'][name];w=np.array([z['weights'][a] for a in A]);cv=np.cov(r.tail(60).values,rowvar=False)*12
 rc=w*(cv@w)/(w@cv@w)
 if name=='Fixed risk parity':assert max(abs(rc-1/6))<1e-7
 assert abs(np.sqrt(w@cv@w)-s['current_risk'][name]['volatility'])<1e-12
(P/'Results/backtest_verification.json').write_text(json.dumps({'passed':True,'source_price_returns_rebuilt':True,'monthly_returns_checked':checks,'dollar_accounting_reconciliation_max_error':float(largest),'training_inputs_precede_frozen_tests':True,'current_proposal_test_is_retrospective':True,'untouched_historical_holdout':False},indent=2))
print('Verified',checks,'monthly observations against independent dollar accounting and source-price returns.')
