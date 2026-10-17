"""Fixed SAA retrospective simulation and chronology-respecting historical fits."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
P=Path(__file__).resolve().parents[1]
A=['SPY','EEMV','DBC','VGSH','SCHD','STIP']
R=pd.read_csv(P/'Data/monthly_returns.csv',index_col=0,parse_dates=True)[A]
RF=pd.read_csv(P/'Data/risk_free_monthly.csv',index_col=0,parse_dates=True).monthly_rf_proxy
CAPITAL=100_000_000
COST=.001

def risk(w,v):return w*(v@w)/(w@v@w)
def parity(v):
 n=len(v);scaled=v/np.mean(np.diag(v));b=np.ones(n)/n
 q=minimize(lambda x:.5*x@scaled@x-b@np.log(x),np.ones(n),jac=lambda x:scaled@x-b/x,bounds=[(1e-10,None)]*n,method='L-BFGS-B',options={'ftol':1e-15,'gtol':1e-10,'maxiter':3000})
 w=q.x/q.x.sum();assert max(abs(risk(w,v)-b))<1e-7
 return w

def optimize(h):
 v=h.cov().values*12;mu=h.mean().values*12;n=len(A)
 def jr(w):
  z=v@w;variance=w@z
  return (np.diag(z)+np.diag(w)@v)/variance-np.outer(w*z,2*z)/variance**2
 groups=[([0,4],.05),([1],.05),([2],.05),([3],.05),([5],.05),([3,5],.20)]
 eq=np.isin(np.arange(n),[0,1,4]).astype(float)
 seeds=[];attempts=[]
 for target in [.08,.075,.07]:
  cons=[{'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(n)}, {'type':'eq','fun':lambda w,t=target:(w@v@w)/(t*t)-1,'jac':lambda w,t=target:2*v@w/(t*t)}, {'type':'ineq','fun':lambda w:.65-eq@risk(w,v),'jac':lambda w:-eq@jr(w)}, {'type':'ineq','fun':lambda w:.40-risk(w,v),'jac':lambda w:-jr(w)}]
  for ids,floor in groups:
   m=np.isin(np.arange(n),ids).astype(float);cons.append({'type':'ineq','fun':lambda w,m=m,f=floor:m@w-f,'jac':lambda w,m=m:m})
  good=[];seeds=[]
  for seed in [12,91]:
   local=[]
   for x in np.random.default_rng(seed).dirichlet(np.ones(n),100):
    z=minimize(lambda w:-mu@w,x,jac=lambda w:-mu,bounds=[(0,.35)]*n,constraints=cons,method='SLSQP',options={'ftol':1e-11,'maxiter':400})
    if z.success and abs(z.x.sum()-1)<1e-7 and abs(np.sqrt(z.x@v@z.x)-target)<1e-7 and min(np.min(c['fun'](z.x)) for c in cons if c['type']=='ineq')>=-1e-7:local.append(z)
   seeds.append(min(q.fun for q in local) if local else None);good.extend(local)
  attempts.append({'target':target,'seed_objectives':seeds})
  if good:
   w=min(good,key=lambda q:q.fun).x
   return w,{'target':target,'seed_objectives':seeds,'attempts':attempts,'fit_first':str(h.index[0].date()),'fit_last':str(h.index[-1].date()),'estimated_volatility':float(np.sqrt(w@v@w)),'weights':dict(zip(A,w)),'risk_shares':dict(zip(A,risk(w,v)))}
 raise RuntimeError('No verified fixed-SAA solution within the volatility band')

def simulate(w,returns,cost=COST):
 """Rebalance from drifted holdings to the fixed target before each return month."""
 prev=np.zeros(len(A));rows=[]
 for day,x in returns.iterrows():
  gross=float(w@x.values);traded=float(abs(w-prev).sum());net=(1-cost*traded)*(1+gross)-1
  rows.append([day,gross,traded,net]);prev=w*(1+x.values)/(1+gross)
 return pd.DataFrame(rows,columns=['month','gross_return','dollars_traded_per_dollar_nav','net_return']).set_index('month')

def metrics(x):
 rf=RF.reindex(x.index);assert rf.notna().all();vol=float(x.std(ddof=1)*np.sqrt(12));wealth=np.cumprod(np.r_[1,1+x.values]);dd=wealth/np.maximum.accumulate(wealth)-1
 return {'months':len(x),'cagr':float(wealth[-1]**(12/len(x))-1),'annualized_mean_return':float(x.mean()*12),'volatility':vol,'sharpe':float((x-rf).mean()*12/vol),'max_month_end_drawdown':float(min(dd)),'historical_one_month_95pct_var':float(-x.quantile(.05)),'historical_var_usd':float(-x.quantile(.05)*CAPITAL),'normal_zero_mean_one_month_95pct_var':float(1.6448536269514722*vol/np.sqrt(12)),'worst_month':float(x.min()),'terminal_value_usd':float(CAPITAL*wealth[-1])}

def suite(weights,data):
 out={};series={}
 for name,w in weights.items():
  f=simulate(w,data);series[name]=f.net_return
  out[name]={'weights':dict(zip(A,w)),'statistics':metrics(f.net_return),'no_cost_statistics':metrics(simulate(w,data,0).net_return),'higher_cost_statistics':metrics(simulate(w,data,.0025).net_return),'annual_traded_fraction':float(f.dollars_traded_per_dollar_nav.mean()*12)}
 return out,pd.DataFrame(series)

if __name__=='__main__':
 d=json.loads((P/'Results/recommended_weights.json').read_text());current=np.array([d['rounded_weights'][a] for a in A]);h=R.tail(60);v=h.cov().values*12
 current_weights={'Proposed fixed MVO':current,'Fixed equal weight':np.ones(6)/6,'Fixed risk parity':parity(v)}
 result={'protocol':{'target_weight_rule':'Fix weights once at inception; restore those targets monthly','final_weight_fit':'October 2021 to September 2026','primary_period':'November 2016 to September 2026','cost':COST,'higher_cost':.0025,'rf':'FRED DGS1MO prior-month yield-accrual proxy','selection_bias':'All historical data had been inspected; no historical interval is an untouched team selection holdout. Historical validation fits exclude their subsequent evaluation returns but the universe and policy are retrospective.','universe':'Six currently selected ETFs held constant across all three comparator rules','alternative_eligible_etf':'VWO remains eligible in the original current optimizer but received zero. This six-fund test is conditional on the selected holdings.'},'current_risk':{name:{'volatility':float(np.sqrt(w@v@w)),'risk_shares':dict(zip(A,risk(w,v)))} for name,w in current_weights.items()}}
 start=pd.Timestamp('2016-11-30');data=R.loc[start:]
 result['fixed_proposal_retrospective'],series=suite(current_weights,data);series.to_csv(P/'Results/fixed_proposal_monthly_returns.csv')
 result['fixed_proposal_subperiods']={label:{name:metrics(series.loc[lo:hi,name]) for name in series} for label,lo,hi in [('Older_history_diagnostic','2016-11','2021-09'),('Current_fit_window','2021-10','2026-09')]}
 for label,begin in [('historical_fit_2016','2016-11-30'),('historical_fit_2021','2021-11-30')]:
  begin=pd.Timestamp(begin);train=R.loc[R.index<begin].tail(60);assert len(train)==60 and train.index[-1]<begin
  w,fit=optimize(train);cv=train.cov().values*12;weights={'Frozen trained MVO':w,'Frozen equal weight':np.ones(6)/6,'Frozen trained risk parity':parity(cv)}
  out,frame=suite(weights,R.loc[begin:]);result[label]={'training':fit,'evaluation_first':str(begin.date()),'evaluation_last':str(R.index[-1].date()),'strategies':out,'inception_risk':{name:float(np.sqrt(q@cv@q)) for name,q in weights.items()}}
  frame.to_csv(P/f'Results/{label}_monthly_returns.csv');print(label,fit,flush=True)
 x=series['Proposed fixed MVO'];rng=np.random.default_rng(20261014);rf=RF.reindex(x.index).values;est=[];n=len(x);block=6
 for _ in range(3000):
  idx=np.concatenate([(j+np.arange(block))%n for j in rng.integers(0,n,size=(n+block-1)//block)])[:n];q=x.values[idx];est.append(float((q-rf[idx]).mean()/q.std(ddof=1)*np.sqrt(12)))
 result['uncertainty']={'bootstrap_block_months':6,'replications':3000,'retrospective_sharpe_95pct_interval':np.quantile(est,[.025,.975]).tolist(),'does_not_correct_selection_bias':True}
 (P/'Results/backtest_results.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result['fixed_proposal_retrospective'],indent=2),flush=True)
