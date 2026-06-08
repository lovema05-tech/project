import unittest
import os
import shutil
from database import init_db, get_connection, enroll_student, get_student_sort_key

class TestDisplacementLogic(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup clean test db
        init_db()
        
    def test_priority_ranking(self):
        # Mock students data
        student_a = {
            "student_email": "a@daeyang.hs.kr",
            "unexcused_absences": 0,
            "unexcused_tardiness": 0,
            "sick_absences": 0,
            "sick_tardiness": 0,
            "sick_early_leaves": 0,
            "created_at": "2026-06-08T10:00:00"
        }
        
        student_b = {
            "student_email": "b@daeyang.hs.kr",
            "unexcused_absences": 0,
            "unexcused_tardiness": 1, # -3 points penalty
            "sick_absences": 0,
            "sick_tardiness": 0,
            "sick_early_leaves": 0,
            "created_at": "2026-06-08T10:00:00"
        }
        
        student_c = {
            "student_email": "c@daeyang.hs.kr",
            "unexcused_absences": 1, # -5 points penalty
            "unexcused_tardiness": 0,
            "sick_absences": 0,
            "sick_tardiness": 0,
            "sick_early_leaves": 0,
            "created_at": "2026-06-08T10:00:00"
        }
        
        student_d = {
            "student_email": "d@daeyang.hs.kr",
            "unexcused_absences": 0,
            "unexcused_tardiness": 0,
            "sick_absences": 1, # 0 penalty points, but 1 sick absence
            "sick_tardiness": 0,
            "sick_early_leaves": 0,
            "created_at": "2026-06-08T10:00:00"
        }
        
        student_e = {
            "student_email": "e@daeyang.hs.kr",
            "unexcused_absences": 0,
            "unexcused_tardiness": 0,
            "sick_absences": 0,
            "sick_tardiness": 0,
            "sick_early_leaves": 0,
            "created_at": "2026-06-08T10:05:00" # Applied 5 minutes later than student_a
        }
        
        # Priority should be:
        # 1. student_a (Perfect, applied early) -> Key: (0, 0, 0, 0, '2026-06-08T10:00:00')
        # 2. student_e (Perfect, applied late) -> Key: (0, 0, 0, 0, '2026-06-08T10:05:00')
        # 3. student_d (0 penalty, 1 sick leave) -> Key: (0, 1, 0, 0, '2026-06-08T10:00:00')
        # 4. student_b (-3 penalty) -> Key: (3, 0, 0, 0, '2026-06-08T10:00:00')
        # 5. student_c (-5 penalty) -> Key: (5, 0, 0, 0, '2026-06-08T10:00:00')
        
        candidates = [student_c, student_b, student_e, student_d, student_a]
        candidates.sort(key=get_student_sort_key)
        
        self.assertEqual(candidates[0]['student_email'], "a@daeyang.hs.kr")
        self.assertEqual(candidates[1]['student_email'], "e@daeyang.hs.kr")
        self.assertEqual(candidates[2]['student_email'], "d@daeyang.hs.kr")
        self.assertEqual(candidates[3]['student_email'], "b@daeyang.hs.kr")
        self.assertEqual(candidates[4]['student_email'], "c@daeyang.hs.kr")
        print("Test passed: Ranking is correctly evaluated based on unexcused, sick leave, and timestamps.")

if __name__ == "__main__":
    unittest.main()
