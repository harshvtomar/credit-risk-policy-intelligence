from common import *
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.calibration import calibration_curve

def generate(seed=73):
    rng=np.random.default_rng(seed);n=10000
    month=rng.integers(0,24,n);income=rng.lognormal(10.9,.48,n).clip(15000,250000)
    dti=rng.beta(2,5,n);score=rng.normal(670,65,n).clip(350,850)
    loan=rng.lognormal(9.6,.65,n).clip(1000,75000)
    delinq=rng.poisson(.3,n);employment=rng.choice(['Salaried','Self employed','Contract'],n,p=[.65,.22,.13]);group=rng.choice(['Group A','Group B'],n,p=[.55,.45])
    logit=-2.5+3*dti+(650-score)/75+loan/income*.8+delinq*.5+(employment=='Contract')*.35+np.maximum(month-12,0)*.025
    probability=1/(1+np.exp(-logit));default=rng.binomial(1,probability)
    frame=pd.DataFrame({'application_id':np.arange(1,n+1),'origination_month':[(pd.Timestamp('2023-01-01')+pd.DateOffset(months=int(m))).strftime('%Y-%m') for m in month],'annual_income':income.round(2),'debt_to_income':dti.round(5),'credit_score':score.round(0),'loan_amount':loan.round(2),'prior_delinquencies':delinq,'employment':employment,'audit_group':group,'default_12m':default})
    frame.loc[rng.choice(n,150,replace=False),'annual_income']=np.nan
    frame=frame.sort_values(['origination_month','application_id']).reset_index(drop=True)
    frame.to_csv(DATA/'applications.csv',index=False);return frame

def analyze():
    df=generate();store_db({'applications':df})
    train=df[df.origination_month<'2024-01'];valid=df[(df.origination_month>='2024-01')&(df.origination_month<'2024-07')];test=df[df.origination_month>='2024-07']
    numeric=['annual_income','debt_to_income','credit_score','loan_amount','prior_delinquencies'];features=numeric+['employment']
    transform=ColumnTransformer([('numeric',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric),('category',OneHotEncoder(handle_unknown='ignore'),['employment'])])
    model=Pipeline([('preprocess',transform),('classifier',LogisticRegression(max_iter=1500,random_state=73))]);model.fit(train[features],train.default_12m)
    valid_p=model.predict_proba(valid[features])[:,1]
    # Hypothetical unit economics: 12% nondefault contribution, 65% loss given default.
    # Denied applicants have zero modeled lender contribution. Threshold is selected on validation only.
    thresholds=[]
    for threshold in np.arange(.02,.51,.01):
        approve=valid_p<threshold
        pnl=np.where(valid.default_12m==0,valid.loan_amount*.12,-valid.loan_amount*.65)
        thresholds.append([float(threshold),float(pnl[approve].sum()),float(approve.mean())])
    policy=pd.DataFrame(thresholds,columns=['threshold','validation_contribution','approval_rate']);save_table(policy,'threshold_sweep')
    threshold=float(policy.loc[policy.validation_contribution.idxmax(),'threshold'])
    scored=test.copy();scored['predicted_pd']=model.predict_proba(test[features])[:,1];scored['approved']=(scored.predicted_pd<threshold).astype(int);scored['funded_amount']=scored.loan_amount*scored.approved;scored['approved_defaults']=scored.default_12m*scored.approved;scored['realized_contribution']=np.where(scored.default_12m==0,scored.loan_amount*.12,-scored.loan_amount*.65)*scored.approved
    save_table(scored,'test_predictions')
    summary={'train_rows':len(train),'validation_rows':len(valid),'test_rows':len(test),'test_roc_auc':float(roc_auc_score(test.default_12m,scored.predicted_pd)),'test_average_precision':float(average_precision_score(test.default_12m,scored.predicted_pd)),'test_brier_score':float(brier_score_loss(test.default_12m,scored.predicted_pd)),'test_prevalence':float(test.default_12m.mean()),'policy_threshold':threshold,'test_approval_rate':float(scored.approved.mean()),'test_policy_contribution':float(scored.realized_contribution.sum()),'approve_all_contribution':float(np.where(test.default_12m==0,test.loan_amount*.12,-test.loan_amount*.65).sum()),'observation_cutoff':'2025-12-31'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    monthly=scored.groupby(['origination_month','employment']).agg(applications=('application_id','size'),defaults=('default_12m','sum'),approved=('approved','sum'),approved_defaults=('approved_defaults','sum'),funded_amount=('funded_amount','sum'),contribution=('realized_contribution','sum')).reset_index().rename(columns={'origination_month':'month','employment':'segment'})
    monthly['default_rate']=monthly.defaults/monthly.applications;save_table(monthly,'monthly_kpis')
    audits=[]
    for group,g in scored.groupby('audit_group'):
        bad=g.default_12m==1;good=~bad;rejected=g.approved==0
        audits.append({'group':group,'n':len(g),'default_rate':float(bad.mean()),'approval_rate':float(g.approved.mean()),'rejection_tpr':float(rejected[bad].mean()),'rejection_fpr':float(rejected[good].mean()),'brier':float(brier_score_loss(g.default_12m,g.predicted_pd))})
    audit=pd.DataFrame(audits);save_table(audit,'group_audit')
    observed,predicted=calibration_curve(test.default_12m,scored.predicted_pd,n_bins=10,strategy='quantile');save_table(pd.DataFrame({'mean_predicted_pd':predicted,'observed_default_rate':observed}),'calibration')
    drift=[]
    for col in numeric:
        edges=np.unique(np.r_[-np.inf,np.quantile(train[col].dropna(),np.arange(.1,1,.1)),np.inf])
        tr=np.histogram(train[col].dropna(),bins=edges)[0];te=np.histogram(test[col].dropna(),bins=edges)[0]
        a=(tr+.5)/(tr.sum()+.5*len(tr));b=(te+.5)/(te.sum()+.5*len(te));psi=float(((b-a)*np.log(b/a)).sum())
        drift.append({'feature':col,'psi':psi,'train_missing_rate':float(train[col].isna().mean()),'test_missing_rate':float(test[col].isna().mean())})
    save_table(pd.DataFrame(drift),'feature_drift')
    coef=pd.DataFrame({'feature':model.named_steps['preprocess'].get_feature_names_out(),'coefficient':model.named_steps['classifier'].coef_[0]});save_table(coef,'model_coefficients')
    chart(monthly.groupby('month',as_index=False).agg(applications=('applications','sum'),defaults=('defaults','sum')).assign(default_rate=lambda x:x.defaults/x.applications),'month','default_rate','Test-period default rate','default_trend.png')
    fig,ax=plt.subplots(figsize=(6,5),layout='constrained');ax.plot(predicted,observed,'o-',label='Test calibration');ax.plot([0,1],[0,1],'--',color='gray',label='Perfect calibration');ax.set(xlabel='Predicted PD',ylabel='Observed default rate',title='Out-of-time calibration');ax.legend();fig.savefig(OUT/'calibration.png',dpi=140);plt.close(fig)
    metrics=[dict(label='Applications',numerator='applications',unit='number'),dict(label='Default rate',numerator='defaults',denominator='applications',unit='percent'),dict(label='Approval rate',numerator='approved',denominator='applications',unit='percent'),dict(label='Policy contribution',numerator='contribution',unit='usd')]
    save_dashboard(monthly.to_dict('records'),metrics,metrics[1],'Credit Risk & Policy Intelligence','Out-of-time credit analysis, validation-selected lending policy, calibration, and group audits. Dashboard covers July–December 2024 originations; outcomes mature through December 2025. Simulated USD.',{},[dict(key='month',label='Month'),dict(key='segment',label='Employment'),dict(key='applications',label='Applications',unit='number'),dict(key='default_rate',label='Default rate',unit='percent'),dict(key='approved',label='Approved',unit='number'),dict(key='contribution',label='Contribution',unit='usd')])
    (OUT/'executive_brief.md').write_text(f'''# Credit risk decision brief\n\nSynthetic educational analysis. No deployment or real lending recommendation.\n\n- Out-of-time ROC AUC: {summary['test_roc_auc']:.3f}; average precision: {summary['test_average_precision']:.3f}, compared with default prevalence {summary['test_prevalence']:.1%}. Brier score: {summary['test_brier_score']:.3f}.\n- Validation selects a PD cutoff of {threshold:.2f}; the held-out test approval rate is {summary['test_approval_rate']:.1%}.\n- Test policy contribution: ${summary['test_policy_contribution']:,.0f}; approve-all comparison: ${summary['approve_all_contribution']:,.0f}. These depend on assumed 12% nondefault contribution and 65% loss given default, not comprehensive loan cash flows.\n- Review calibration and group rejection error rates before considering any operational pilot. Group attributes are excluded from model features; this alone does not establish fairness.\n\nAll simulated applicants have outcomes, including those rejected by the hypothetical policy. Real underwriting data typically lacks rejected-applicant outcomes, so this comparison cannot directly transfer to production. The dataset contains fully matured 12-month outcomes; cutoff is December 2025. Missing-income imputation is fitted on training data only. Group differences have no significance or causal claim.\n''')
    return summary

if __name__=='__main__': print(json.dumps(analyze(),indent=2))
