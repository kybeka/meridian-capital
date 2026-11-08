"""Replays and forward risk validation at fixed, currently selected weights."""
import json
import numpy as np
import pandas as pd
from valuation import OUT, STOCKS, ROOT, ETFS, SAA, data
import replay_methods as vm

def run():
    research=json.loads((OUT/'portfolio.json').read_text())
    p,d,m,ex=data(STOCKS)
    vm.TICKERS=ETFS+STOCKS
    vm.BENCH=np.r_[SAA,np.zeros(len(STOCKS))]
    weights={r['name']:np.array(r['weights'])for r in research['comparisons']}
    frames=[];summaries=[]
    for h in [14,20,33,63]:
        frame=vm.run_windows(p,d,weights,h)
        frames.append(frame)
        summaries.extend(vm.summarize_windows(frame,h))
    pd.concat(frames,ignore_index=True).to_csv(OUT/'staggered_windows.csv',index=False)
    (OUT/'window_summary.json').write_text(json.dumps(summaries,indent=2,allow_nan=False))
    forwards=[]
    for pos in range(59,len(m)):
        origin=m.index[pos]
        train_m=m.iloc[pos-59:pos+1]
        train_d=d.loc[:origin]
        if len(train_d)<252:continue
        future=d.loc[d.index>origin]
        estimates=vm.cov_estimators(train_m,train_d)
        for h in [14,33]:
            if len(future)<h:continue
            test=future.iloc[:h];end=test.index[-1];reg=vm.regime(origin,end)
            for name,w in weights.items():
                delta=w-vm.BENCH
                actual=float(np.std(test.to_numpy()@delta,ddof=1)*252**.5)
                for estimator,cov in estimates.items():
                    pred=float(np.sqrt(max(delta@cov@delta,0)))
                    forwards.append(dict(candidate=name,estimator=estimator,horizon=h,origin=str(origin.date()),end=str(end.date()),regime=reg,
                        train_start=str(train_m.index[0].date()),train_end=str(train_m.index[-1].date()),
                        post_change_training_months=int((train_m.index>=vm.CHANGE).sum()),
                        test_first=str(test.index[0].date()),pred_te=pred,realized_te=actual,
                        pred_within_band=bool(.02<=pred<=.05),realized_above_5=bool(actual>.05),te_underestimated=bool(actual>pred)))
    forecasts=pd.DataFrame(forwards);forecasts.to_csv(OUT/'forward_risk.csv',index=False)
    fs=[]
    for h in [14,33]:
        for r in vm.summarize_forecasts(forecasts[forecasts.horizon==h]):fs.append(dict(horizon=h,**r))
    (OUT/'forward_summary.json').write_text(json.dumps(fs,indent=2,allow_nan=False))
    mf,ms=vm.monthly_forward(m,weights);mf.to_csv(OUT/'monthly_forward.csv',index=False)
    (OUT/'monthly_forward_summary.json').write_text(json.dumps(ms,indent=2,allow_nan=False))
    # No performance claim is based on the windows used in candidate selection.
    # Selection does not use replay returns at all, but the universe/assumptions
    # were researched now, so this remains a hindsight portfolio replay.
    checks={'forward_origins_strictly_before_test':bool((pd.to_datetime(forecasts.train_end)<pd.to_datetime(forecasts.test_first)).all()),
        'sixty_month_training':True,'fees_in_baseline':0,
        'horizons':[14,20,33,63], 'dbc_change':'2025-11-10',
        'replay_status':'Reused history with today-selected securities and weights, not point-in-time alpha validation.',
        'cash_convention':'Adjusted-price total-return proxy reinvests distributions. Bloomberg holdings hold distribution cash. This is not an exact share-account replay.'}
    assert checks['forward_origins_strictly_before_test']
    (OUT/'validation_checks.json').write_text(json.dumps(checks,indent=2))
    for r in summaries:
        if r['regime']=='post' and r['horizon']==33 and r['candidate'] in ['Recorded portfolio target','Entered holdings']:
            print(r['candidate'], 'starts',r['n_overlapping'],'active',r['mean_active'],'win',r['outperform_rate'],'nonoverlap',r['nonoverlap_n_min'],r['nonoverlap_n_max'])
    return summaries,fs,ms

if __name__=='__main__':run()
