import sys
import os

# Include parent directory in python path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Redirect database path to a temporary test database file
import database
test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_curriculum.db")
database.DB_PATH = test_db_path

from database import (
    init_db, get_courses, enroll_student, 
    get_enrollments_by_course, get_connection
)

def run_test():
    # 1. Initialize clean test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    print("1. 테스트 전용 데이터베이스 초기화 및 로드...")
    init_db()
    
    # Let's adjust the capacity of 'e스포츠 코스' to 5 for testing displacement
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET capacity = 5 WHERE name = 'e스포츠 코스'")
    conn.commit()
    conn.close()
    
    courses = get_courses()
    course = next(c for c in courses if c['name'] == "e스포츠 코스")
    course_id = course['id']
    print(f"대상 과목: {course['name']} (테스트 정원: {course['capacity']}명)\n")
    
    # 2. Register 5 students (fill the course to capacity)
    # student1 (Perfect: 0), student2 (Tardiness 1: -3), student4 (Sick Abs 1: 0), student5 (Sick Tardiness 2: 0), student8 (Perfect: 0)
    fill_emails = [
        "student1@daeyang.hs.kr",
        "student2@daeyang.hs.kr",
        "student4@daeyang.hs.kr",
        "student5@daeyang.hs.kr",
        "student8@daeyang.hs.kr"
    ]
    
    print("2. 5명의 학생으로 정원 채우는 중...")
    for email in fill_emails:
        res = enroll_student(email, course_id)
        print(f" - {email} 신청 결과: {res['success']} ({res['message']})")
        
    print("\n현재 수강신청된 학생 명단:")
    enrolled = get_enrollments_by_course(course_id)
    for i, s in enumerate(enrolled):
        print(f" [{i+1}] {s['student_name']} ({s['student_email']}) - 미인정결석: {s['unexcused_absences']}회, 미인정지각: {s['unexcused_tardiness']}회 (감점 점수: {s['unexcused_absences'] * -5 + s['unexcused_tardiness'] * -3}점)")
        
    # 3. Try enrolling student3 (unexcused absence 1: -5 points)
    # This is worse than student2 (-3 points), so student3 should be rejected.
    print(f"\n3. 감점 점수가 더 안 좋은 student3 (-5점)가 추가 신청을 시도합니다...")
    res_rejected = enroll_student("student3@daeyang.hs.kr", course_id)
    print(f" - 결과: {res_rejected['success']} -> {res_rejected['message']}")
    
    # 4. Try enrolling student6 (0 points, sick early leave 1)
    # This is better than student2 (-3 points), so student2 should be kicked out, and student6 enrolled.
    print(f"\n4. 출결 점수가 더 좋은 student6 (0점)가 추가 신청을 시도합니다...")
    res_displaced = enroll_student("student6@daeyang.hs.kr", course_id)
    print(f" - 결과: {res_displaced['success']} -> {res_displaced['message']}")
    if 'kicked_student' in res_displaced:
        print(f"   ▶ 밀려난 학생: {res_displaced['kicked_student']['name']} ({res_displaced['kicked_student']['email']})")
        
    print("\n밀어내기 처리 후 최종 수강신청 학생 명단:")
    enrolled_final = get_enrollments_by_course(course_id)
    for i, s in enumerate(enrolled_final):
        print(f" [{i+1}] {s['student_name']} ({s['student_email']}) - 미인정결석: {s['unexcused_absences']}회, 미인정지각: {s['unexcused_tardiness']}회 (감점 점수: {s['unexcused_absences'] * -5 + s['unexcused_tardiness'] * -3}점)")

    # Clean up test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("\n테스트 종료 후 임시 데이터베이스 삭제 완료.")

if __name__ == "__main__":
    run_test()
