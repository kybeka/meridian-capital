"""Reproduce the final constrained MVO with seven eligible ETFs and no XLE."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
P=Path(__file__).resolve().parents[1]
A=['SPY','VWO','EEMV','DBC','SCHD','VGSH','STIP']
h=pd.read_csv(P/'Data/monthly_returns.csv',index_col=0)[A].tail(60)
V=h.cov().values*12;mu=h.mean().values*12;n=len(A)
def risk(w):return w*(V@w)/(w@V@w)
def derivative(w):
 z=V@w;q=w@z
 return (np.diag(z)+np.diag(w)@V)/q-np.outer(w*z,2*z)/q**2
stocks=np.isin(np.arange(n),[0,1,2,4]).astype(float)
constraints=[{'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(n)}, {'type':'eq','fun':lambda w:w@V@w/.0064-1,'jac':lambda w:2*V@w/.0064}, {'type':'ineq','fun':lambda w:.65-stocks@risk(w),'jac':lambda w:-stocks@derivative(w)}, {'type':'ineq','fun':lambda w:.4-risk(w),'jac':lambda w:-derivative(w)}]
for ids,floor in [([0,4],.05),([1,2],.05),([3],.05),([5],.05),([6],.05),([5,6],.20)]:
 mask=np.isin(np.arange(n),ids).astype(float)
 constraints.append({'type':'ineq','fun':lambda w,m=mask,f=floor:m@w-f,'jac':lambda w,m=mask:m})
solutions=[];seed_scores=[]
for seed in [12,91]:
 valid=[]
 for x in np.random.default_rng(seed).dirichlet(np.ones(n),100):
  z=minimize(lambda w:-mu@w,x,jac=lambda w:-mu,bounds=[(0,.35)]*n,constraints=constraints,method='SLSQP',options={'ftol':1e-11,'maxiter':400})
  if z.success and abs(z.x.sum()-1)<1e-7 and abs(np.sqrt(z.x@V@z.x)-.08)<1e-7 and min(np.min(c['fun'](z.x)) for c in constraints if c['type']=='ineq')>=-1e-7:valid.append(z)
 if not valid:raise RuntimeError('No verified current solution for seed '+str(seed))
 seed_scores.append(float(min(q.fun for q in valid)));solutions.extend(valid)
w=min(solutions,key=lambda q:q.fun).x
rounded=np.round(w,4);rounded[-1]=1-rounded[:-1].sum()
assert rounded.min()>=0 and abs(rounded.sum()-1)<1e-12 and np.sqrt(rounded@V@rounded)<=.08+1e-9 and risk(rounded).max()<=.4+1e-9
record=json.loads((P/'Results/recommended_weights.json').read_text())['rounded_weights']
assert max(abs(rounded[i]-record[a]) for i,a in enumerate(A))<1e-10
out={'eligible_assets':A,'excluded_asset':'XLE','fit_months':60,'fit_first':str(h.index[0]),'fit_last':str(h.index[-1]),'exact_weights':dict(zip(A,w)),'rounded_weights':dict(zip(A,rounded)),'rounded_volatility':float(np.sqrt(rounded@V@rounded)),'rounded_risk_shares':dict(zip(A,risk(rounded))),'seed_objectives':seed_scores,'formal_global_optimum_proven':False,'saved_recommendation_reproduced':True}
(P/'Results/current_optimizer_verification.json').write_text(json.dumps(out,indent=2));print('Verified current optimizer and identical rounded allocation.')
