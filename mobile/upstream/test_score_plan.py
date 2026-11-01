import unittest
from score_plan import build_plan,correct_count

class Tests(unittest.TestCase):
    def setUp(self):
        self.q=[{'id':str(i),'optionList':[{'id':'a'},{'id':'b'}]} for i in range(5)]
    def test_boundaries_and_fractional_points(self):
        for score,count in [(0,0),(3,2),(7.5,5)]:
            plan=build_plan(self.q,lambda _: 'a',score,'1.5')
            self.assertEqual(sum(p['plannedCorrect'] for p in plan),count)
            self.assertEqual(sum(p['answerIds']=='a' for p in plan),count)
    def test_invalid_targets(self):
        for target,points in [(-1,1),(9,1),(2.1,1),(1,0),('NaN',1),('inf',1)]:
            with self.assertRaises(ValueError): correct_count(target,points,5)
    def test_missing_and_stale_bank_rejected(self):
        for answer in (None,'outdated'):
            with self.assertRaises(ValueError): build_plan(self.q,lambda _: answer,2)
    def test_all_correct_multi_option_wrong_answer(self):
        p=build_plan(self.q,lambda _: 'a,b',0)
        self.assertTrue(all(x['answerIds']=='a' for x in p))

if __name__=='__main__':unittest.main()
