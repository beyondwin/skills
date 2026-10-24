import unittest
from review_metrics import score, exact_paired_p, compare_repetitions

class ReviewMetricsTests(unittest.TestCase):
    def setUp(self):
        self.gold=[{'id':'positive','eligible':True,'category':'valid'},{'id':'negative','eligible':False,'category':'count'}]
    def obs(self,a,b):return [{'id':'positive','eligible':a},{'id':'negative','eligible':b}]
    def test_perfect(self):
        r=score(self.gold,self.obs(True,False));self.assertEqual((r['correct'],r['false_accept'],r['false_reject']),(2,0,0))
    def test_false_accept_and_reject_separate(self):
        r=score(self.gold,self.obs(False,True));self.assertEqual((r['false_accept'],r['false_reject']),(1,1))
    def test_missing_retains_denominator(self):
        r=score(self.gold,[]);self.assertEqual((r['total'],r['clear'],r['missing'],r['correct'],r['false_reject']),(2,2,2,0,1))
    def test_positive_hold_false_reject(self):
        r=score(self.gold,[{'id':'positive','eligible':False,'unverified':True}]);self.assertEqual(r['false_reject'],1);self.assertEqual(r['correct'],0)
    def test_negative_hold_not_correct_or_false_accept(self):
        r=score(self.gold,[{'id':'negative','eligible':False,'unverified':True}]);self.assertEqual(r['false_accept'],0);self.assertEqual(r['correct'],0)
    def test_disputed_stays_in_total(self):
        gold=self.gold+[{'id':'unknown','eligible':None,'category':'visibility'}];r=score(gold,self.obs(True,False)+[{'id':'unknown','eligible':True}]);self.assertEqual((r['total'],r['clear'],r['disputed'],r['correct']),(3,2,1,2))
    def test_missing_reference_field_rejected(self):
        with self.assertRaises(ValueError):score([{'id':'p','category':'x'}],[])
    def test_unknown_gold_type_rejected(self):
        with self.assertRaises(ValueError):score([{'id':'p','eligible':'unknown','category':'x'}],[])
    def test_extra_id_rejected(self):
        with self.assertRaises(ValueError):score(self.gold,[{'id':'extra','eligible':False}])
    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):score(self.gold,self.obs(True,False)*2)
    def test_null_observation_rejected(self):
        with self.assertRaises(ValueError):score(self.gold,[{'id':'positive','eligible':None}])
    def test_contradictory_pass_rejected(self):
        with self.assertRaises(ValueError):score(self.gold,[{'id':'positive','eligible':True,'unverified':True}])
    def test_categories_preserve_unscored(self):
        r=score(self.gold,[]);self.assertEqual(r['categories']['count'],{'total':1,'clear':1,'correct':0,'errors':1})
    def test_exact_paired_test(self):
        self.assertEqual(exact_paired_p(6,0),.03125);self.assertEqual(exact_paired_p(0,0),1);self.assertEqual(exact_paired_p(2,2),1)
    def test_repetitions_are_not_independent_images(self):
        r=compare_repetitions(self.gold,[self.obs(False,True)]*2,[self.obs(True,False)]*2);self.assertEqual((r['unique_population'],r['unique_improved'],r['unique_exact_paired_p']),(2,2,.5))
    def test_each_repeat_reported(self):
        r=compare_repetitions(self.gold,[self.obs(False,True)]*2,[self.obs(True,False),self.obs(False,True)]);self.assertEqual([x['net_correct_gain'] for x in r['repetitions']],[2,0]);self.assertEqual(r['unique_improved'],2)
    def test_disputed_never_improvement(self):
        gold=[{'id':'x','eligible':None,'category':'x'}];r=compare_repetitions(gold,[[{'id':'x','eligible':False}]],[[{'id':'x','eligible':True}]]);self.assertEqual(r['unique_improved'],0)
    def test_unequal_repetitions_rejected(self):
        with self.assertRaises(ValueError):compare_repetitions(self.gold,[],[self.obs(True,False)])
if __name__=='__main__':unittest.main()
