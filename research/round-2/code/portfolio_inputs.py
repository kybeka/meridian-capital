from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ETFS=['SPY','EEMV','DBC','SCHD','VGSH','STIP'];SAA=np.array([.2608,.0966,.2695,.0328,.05,.2903])
POLICY=json.loads((ROOT/'data/policies/valuation_policy_v4.json').read_text())
def quotes():
 q={}
 for file in ['quotes_prior.json','quotes_energy.json','quotes.json','quotes_extension.json']:
  for a in json.loads((ROOT/'data'/file).read_text())['quoteResponse']['result']:q[a['symbol']]=a
 return q

def statements(t,freq='annual'):
 raw=json.loads((ROOT/'data/statements'/(t+'.json')).read_text())['timeseries']['result'];cols={}
 for a in raw:
  typ=a['meta']['type'][0]
  if typ.startswith(freq):cols[typ[len(freq):]]={v['asOfDate']:v['reportedValue']['raw'] for v in a.get(typ,[])}
 out=pd.DataFrame(cols).sort_index();out=out[out.TotalRevenue.notna()].copy()
 ledger=ROOT/'data/issuer_overrides.json'
 if ledger.exists():
  for a in json.loads(ledger.read_text()):
   if a['ticker']==t and a['frequency']==freq and a['period'] in out.index:out.loc[a['period'],a['field']]=a['value']
 if t=='ADBE':out['CashDividendsPaid']=0.
 return out

def ttm(t):
 q=statements(t,'quarterly').tail(4);assert len(q)==4
 out={c:(float(q[c].sum(min_count=4)) if c in q and q[c].notna().sum()==4 else None) for c in ['TotalRevenue','NetIncome','DilutedEPS','OperatingCashFlow','CapitalExpenditure','StockBasedCompensation','CashDividendsPaid','RepurchaseOfCapitalStock']}
 out['as_of']=str(q.index[-1]);out['FCF']=out['OperatingCashFlow']-abs(out['CapitalExpenditure']) if out['OperatingCashFlow'] is not None and out['CapitalExpenditure'] is not None else None
 out['economic_cash']=out['FCF']-out['StockBasedCompensation'] if out['StockBasedCompensation'] is not None else None
 return out

def prices(t):
 raw=json.loads((ROOT/'data/prices'/(t+'.json')).read_text())['chart']['result'][0]
 idx=pd.to_datetime(raw['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
 f=pd.DataFrame({'close':raw['indicators']['quote'][0]['close'],'adjclose':raw['indicators']['adjclose'][0]['adjclose']},index=idx)
 fallback=ROOT/'data/price_fallback'/(t+'.json')
 if fallback.exists():
  a=json.loads(fallback.read_text())['chart']['result'][0];ii=pd.to_datetime(a['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize();f=f.combine_first(pd.DataFrame({'close':a['indicators']['quote'][0]['close'],'adjclose':a['indicators']['adjclose'][0]['adjclose']},index=ii))
 f=f.loc[:'2026-11-06'].dropna()
 for e in json.loads((ROOT/'data/dividend_overrides.json').read_text()):
  if e['ticker']!=t:continue
  ex=pd.Timestamp(e['ex_date']);present=any(pd.Timestamp(v['date'],unit='s',tz='UTC').tz_convert('America/New_York').date()==ex.date() for v in raw.get('events',{}).get('dividends',{}).values())
  if not present:f.loc[f.index<ex,'adjclose']*=1-e['amount']/f.loc[f.index<ex,'close'].iloc[-1]
 assert str(f.index[-1].date())=='2026-11-06',(t,'Missing reference close')
 return f

def cashvalue(C,k,g,g2):
 if k<=g2:return None
 return sum(C*(1+g)**j/(1+k)**j for j in range(1,6))+C*(1+g)**5*(1+g2)/(k-g2)/(1+k)**5

def data(stocks):
 p=pd.DataFrame({t:prices(t).adjclose for t in ETFS+stocks}).dropna()
 d=p.pct_change(fill_method=None).iloc[1:];m=p.resample('ME').last().loc[:'2026-10-31'].pct_change(fill_method=None).dropna()
 rates=pd.read_csv(ROOT/'data/fred_history.csv',index_col=0,parse_dates=True);rf=rates.DGS1MO.resample('ME').mean().reindex(m.index)/1200
 return p,d,m,m.sub(rf,axis=0)

def rows(stocks,m,ex):
 q=quotes();a=[];saa_ex=ex[ETFS].to_numpy()@SAA
 for t in stocks:
  y=ex[t].tail(60).to_numpy();s=saa_ex[-60:];market=ex.SPY.tail(60).to_numpy();beta=np.cov(y,s,ddof=1)[0,1]/np.var(s,ddof=1);bm=np.cov(y,market,ddof=1)[0,1]/np.var(market,ddof=1);res=y-y.mean()-beta*(s-s.mean());ev=np.var(res,ddof=1)*12
  k=POLICY['rf10y']+bm*POLICY['erp'];v=POLICY['valuation'][t];price=round(float(prices(t).close.iloc[-1]),2);value=v['eps']*v['pe'];full=(1+k)*(value/price-1);alpha=POLICY['alpha_fraction']*full;cash=ttm(t);cashbase=v.get('cash_base_override',cash['economic_cash']);cps=cashbase/q[t]['sharesOutstanding'] if cashbase is not None else None
  a.append({'ticker':t,**v,'price':price,'value':value,'gap':value/price-1,'k':k,'beta_market':bm,'beta_saa':beta,'residual_variance':ev,'alpha_full':full,'alpha':alpha,'score':max(alpha,0)/ev,'ttm':cash,'cash_per_share':cps,'cash_crosscheck':cashvalue(cps,k,v['cash_growth'],v['terminal_growth']) if cps is not None else None})
 return a

def covariance_set(d,m):
 a=d.tail(252).to_numpy();ww=2**(-np.arange(len(a))[::-1]/63);ww/=ww.sum();center=a-(a*ww[:,None]).sum(axis=0)
 return {'Monthly60':m.tail(60).cov().to_numpy()*12,'Daily252':d.tail(252).cov().to_numpy()*252,'Daily63':d.tail(63).cov().to_numpy()*252,'EWMA252':center.T@(center*ww[:,None])/(1-(ww*ww).sum())*252}
