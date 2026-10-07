import unittest, json
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
class SharedChecks(unittest.TestCase):
    def test_dashboard_weighted_kpis_reconcile(self):
        payload=json.loads((ROOT/'outputs/dashboard_data.json').read_text())
        raw=pd.read_csv(ROOT/'outputs/monthly_kpis.csv')
        embedded=pd.DataFrame(payload['rows'])
        pd.testing.assert_frame_equal(raw,embedded,check_dtype=False,atol=1e-5,rtol=1e-5)
        for segment in ['All']+list(raw.segment.unique()):
            rows=embedded if segment=='All' else embedded[embedded.segment==segment]
            self.assertGreater(len(rows),0)
            for m in payload['metrics']:
                value=rows[m['numerator']].sum()
                if 'denominator' in m: value/=rows[m['denominator']].sum()
                self.assertTrue(np.isfinite(value))
        html=(ROOT/'dashboard/index.html').read_text()
        self.assertNotIn('__PAYLOAD__',html)
        self.assertNotIn('<script src=',html)
    def test_inputs_primary_keys(self):
        for filename,key in KEYS.items():
            df=pd.read_csv(ROOT/'data'/filename)
            self.assertFalse(df[key].isna().any())
            self.assertFalse(df[key].duplicated().any())

KEYS={'applications.csv':'application_id'}
class CreditChecks(unittest.TestCase):
    def test_temporal_separation_and_outcomes(self):
        source=pd.read_csv(ROOT/'data/applications.csv');scored=pd.read_csv(ROOT/'outputs/test_predictions.csv');summary=json.loads((ROOT/'outputs/summary.json').read_text())
        self.assertTrue((scored.origination_month>='2024-07').all())
        self.assertEqual(summary['train_rows']+summary['validation_rows']+summary['test_rows'],len(source))
        self.assertTrue(source.default_12m.isin([0,1]).all())
        self.assertTrue(scored.predicted_pd.between(0,1).all())
        self.assertLess((pd.Timestamp(source.origination_month.max())+pd.DateOffset(months=12)).strftime('%Y-%m'),summary['observation_cutoff'])
    def test_threshold_selected_on_validation(self):
        sweep=pd.read_csv(ROOT/'outputs/threshold_sweep.csv');summary=json.loads((ROOT/'outputs/summary.json').read_text())
        optimal=sweep.loc[sweep.validation_contribution.idxmax(),'threshold']
        self.assertAlmostEqual(summary['policy_threshold'],optimal)
        pred=pd.read_csv(ROOT/'outputs/test_predictions.csv')
        np.testing.assert_array_equal(pred.approved,(pred.predicted_pd<optimal).astype(int))
    def test_policy_accounting_and_baseline(self):
        scored=pd.read_csv(ROOT/'outputs/test_predictions.csv');summary=json.loads((ROOT/'outputs/summary.json').read_text())
        all_pnl=np.where(scored.default_12m==0,scored.loan_amount*.12,-scored.loan_amount*.65)
        np.testing.assert_allclose(scored.realized_contribution,all_pnl*scored.approved,atol=1e-5)
        self.assertAlmostEqual(summary['approve_all_contribution'],all_pnl.sum(),places=3)
    def test_audit_group_excluded_and_metrics(self):
        coeff=pd.read_csv(ROOT/'outputs/model_coefficients.csv');self.assertFalse(coeff.feature.str.contains('audit_group').any())
        audit=pd.read_csv(ROOT/'outputs/group_audit.csv')
        for col in ['approval_rate','rejection_tpr','rejection_fpr','brier']:
            self.assertTrue(audit[col].between(0,1).all())
        self.assertEqual(audit.n.sum(),len(pd.read_csv(ROOT/'outputs/test_predictions.csv')))
    def test_sql_populations(self):
        sql=pd.read_csv(ROOT/'outputs/sql_result_2.csv').set_index('split');s=json.loads((ROOT/'outputs/summary.json').read_text())
        for split in ['train','validation','test']: self.assertEqual(sql.loc[split,'applications'],s[split+'_rows'])

if __name__=='__main__': unittest.main()
