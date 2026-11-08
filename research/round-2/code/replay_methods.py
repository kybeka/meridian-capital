import json
import numpy as np
import pandas as pd
from portfolio_inputs import ROOT,ETFS,SAA,data,covariance_set
A=json.loads((ROOT/'results/analysis.json').read_text())
TICKERS=list(dict.fromkeys(t for v in A['comparators'].values() for t in v))
BENCH=np.array([dict(zip(ETFS,SAA)).get(t,0.) for t in TICKERS])
CHANGE=pd.Timestamp('2025-11-10')
def regime(start,end):return 'pre' if end<CHANGE else 'post' if start>=CHANGE else 'crossing'
def holding_path(asset_returns,w,bps=0):
 """Unchanged units, reinvested total-return proxies, proportional entry/exit costs."""
 growth=np.vstack([np.ones(len(w)),np.cumprod(1+asset_returns,axis=0)])
 wealth=growth@w;benchmark=growth@BENCH
 entry=np.abs(w-BENCH).sum();endw=w*growth[-1]/wealth[-1];endb=BENCH*growth[-1]/benchmark[-1];exit_=np.abs(endw-endb).sum()
 net=wealth*(1-entry*bps/10000);net[0]=1;net[-1]*=1-exit_*bps/10000
 return wealth,benchmark,net,entry,exit_

def boot_interval(values,h,seed=20261106):
 values=np.asarray(values);n=len(values)
 if n<2:return [None,None]
 rng=np.random.default_rng(seed);block=min(2*h,n);blocks=int(np.ceil(n/block));result=[]
 for _ in range(1000):
  starts=rng.integers(0,n,size=blocks);ix=((starts[:,None]+np.arange(block))%n).ravel()[:n];result.append(values[ix].mean())
 return [float(z) for z in np.quantile(result,[.025,.975])]

def summarize_windows(df,h):
 out=[]
 for (name,reg),part in df.groupby(['candidate','regime'],sort=False):
  out.append(summarize_one(name,reg,part,h))
 for name,part in df.groupby('candidate',sort=False):out.append(summarize_one(name,'all',part,h))
 return out

def summarize_one(name,reg,part,h):
 ar=part.active_net.to_numpy();ret=part.net_return.to_numpy()
 worst=part.loc[part.net_return.idxmin()];phases=[]
 # Each phase uses adjacent non-overlapping holding intervals, not independent phase samples.
 for phase in range(h):
  group=part[part.start_pos.mod(h)==phase]
  if len(group):phases.append({'phase':phase,'n':len(group),'mean_active':float(group.active_net.mean()),'loss_rate':float((group.net_return<0).mean())})
 ordered=np.sort(ret);tail=ordered[:max(1,int(np.ceil(.05*len(ret))))]
 return {'candidate':name,'regime':reg,'horizon':h,'n_overlapping':len(part),'nonoverlap_n_min':min(z['n'] for z in phases),'nonoverlap_n_max':max(z['n'] for z in phases),'start_first':part.start.min(),'end_last':part.end.max(),'median_realized_net_ir':float(part.realized_net_ir.median())if part.realized_net_ir.notna().any()else None,'median_net_return':float(np.median(ret)),'mean_net_return':float(ret.mean()),'loss_rate':float((ret<0).mean()),'outperform_rate':float((ar>0).mean()),'mean_active':float(ar.mean()),'median_active':float(np.median(ar)),'q05_net_return':float(np.quantile(ret,.05)),'expected_shortfall_5':float(tail.mean()),'worst_return':float(ret.min()),'worst_start':worst.start,'worst_end':worst.end,'median_mdd':float(part.mdd.median()),'worst_mdd':float(part.mdd.min()),'active_mean_ci_block':boot_interval(ar,h),'loss_rate_ci_block':boot_interval((ret<0).astype(float),h),'phase_mean_active_min':min(z['mean_active'] for z in phases),'phase_mean_active_max':max(z['mean_active'] for z in phases),'phases':phases}

def run_windows(prices,returns,weights,h):
 a=returns.to_numpy();dates=prices.index;results=[]
 for start in range(len(a)-h+1):
  growth=np.vstack([np.ones(len(BENCH)),np.cumprod(1+a[start:start+h],axis=0)])
  bench=growth@BENCH;startdate=dates[start];enddate=dates[start+h];reg=regime(startdate,enddate)
  for name,w in weights.items():
   wealth=growth@w;entry=np.abs(w-BENCH).sum();exit_=np.abs(w*growth[-1]/wealth[-1]-BENCH*growth[-1]/bench[-1]).sum()
   net=wealth.copy()
   dd=net/np.maximum.accumulate(net)-1
   rp=net[1:]/net[:-1]-1;rb=bench[1:]/bench[:-1]-1;ar=rp-rb;rv=ar.std(ddof=1)*252**.5;real_ir=float(ar.mean()*252/rv)if rv>1e-12 else None
   results.append({'candidate':name,'horizon':h,'start_pos':start,'start':str(startdate.date()),'end':str(enddate.date()),'regime':reg,'gross_return':wealth[-1]-1,'benchmark_return':bench[-1]-1,'net_return':net[-1]-1,'active_net':net[-1]-bench[-1],'mdd':dd.min(),'realized_net_ir':real_ir,'realized_net_te':float(rv),'entry_turnover':entry,'exit_turnover':exit_,**{f'net_{bps}bps':wealth[-1]*(1-entry*bps/10000)*(1-exit_*bps/10000)-1 for bps in [0,5,10,25]}})
 return pd.DataFrame(results)

def cov_estimators(train_m,train_d):
 a=train_d.tail(252).to_numpy();ww=2**(np.arange(len(a))/-63)[::-1];ww/=ww.sum();center=a-np.sum(a*ww[:,None],axis=0)
 return {'Monthly60':train_m.tail(60).cov().to_numpy()*12,'Daily252':train_d.tail(252).cov().to_numpy()*252,'Daily63':train_d.tail(63).cov().to_numpy()*252,'EWMA252_half_life63':(center.T@(center*ww[:,None]))/(1-np.sum(ww*ww))*252}

def summarize_forecasts(frame):
 result=[]
 for name in frame.candidate.unique():
  for estimator in frame.estimator.unique():
   allpart=frame[(frame.candidate==name)&(frame.estimator==estimator)]
   for reg in ['all','pre','post','crossing']:
    p=allpart if reg=='all' else allpart[allpart.regime==reg]
    if p.empty:continue
    eligible=p[p.pred_within_band];ratio=(p.realized_te/p.pred_te.replace(0,np.nan)).dropna()
    result.append({'candidate':name,'estimator':estimator,'regime':reg,'n_overlapping_origins':len(p),'median_pred_te':float(p.pred_te.median()),'median_realized_te':float(p.realized_te.median()),'median_realized_forecast_ratio':float(ratio.median()) if len(ratio) else None,'underestimate_rate':float(p.te_underestimated.mean()),'realized_above_5_rate':float(p.realized_above_5.mean()),'pred_band_count':len(eligible),'realized_breach_given_forecast_pass':float(eligible.realized_above_5.mean()) if len(eligible) else None,'te_rmse':float(np.sqrt(np.mean((p.realized_te-p.pred_te)**2))),'origin_first':p.origin.min(),'origin_last':p.origin.max(),'max_post_change_training_months':int(p.post_change_training_months.max())})
 return result

def monthly_forward(mr,weights):
 """Match the course frequency: preceding60 months predict subsequent6/12 months."""
 rows=[]
 for h in [6,12]:
  for pos in range(59,len(mr)-h):
   train=mr.iloc[pos-59:pos+1];test=mr.iloc[pos+1:pos+h+1];origin=mr.index[pos];end=mr.index[pos+h]
   cov=train.cov().to_numpy()*12
   for name,w in weights.items():
    delta=w-BENCH;pred=float(np.sqrt(max(delta@cov@delta,0)));real=float((test.to_numpy()@delta).std(ddof=1)*12**.5)
    rows.append({'candidate':name,'origin':str(origin.date()),'end':str(end.date()),'horizon_months':h,'regime':regime(origin,end),'train_start':str(train.index[0].date()),'train_end':str(train.index[-1].date()),'test_first':str(test.index[0].date()),'pred_te':pred,'realized_te':real,'pred_band':bool(.02<=pred<=.05),'realized_above5':bool(real>.05)})
 frame=pd.DataFrame(rows);summary=[]
 for (name,h),allpart in frame.groupby(['candidate','horizon_months']):
  for reg in ['all','pre','post','crossing']:
   p=allpart if reg=='all' else allpart[allpart.regime==reg]
   if p.empty:continue
   passing=p[p.pred_band]
   summary.append({'candidate':name,'horizon_months':int(h),'regime':reg,'origins':len(p),'approx_nonoverlap':int(len(p)//h),'median_pred_te':float(p.pred_te.median()),'median_realized_te':float(p.realized_te.median()),'pass_count':len(passing),'realized_above5_given_pass':float(passing.realized_above5.mean()) if len(passing) else None})
 return frame,summary
