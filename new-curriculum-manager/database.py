import os
import sqlite3
import datetime
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "curriculum.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Students Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        email TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        grade INTEGER,
        class INTEGER,
        number INTEGER,
        password TEXT DEFAULT 'dy6400580',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Attendance Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_records (
        student_email TEXT PRIMARY KEY,
        unexcused_absences INTEGER DEFAULT 0,
        unexcused_tardiness INTEGER DEFAULT 0,
        sick_absences INTEGER DEFAULT 0,
        sick_tardiness INTEGER DEFAULT 0,
        sick_early_leaves INTEGER DEFAULT 0,
        FOREIGN KEY (student_email) REFERENCES students(email) ON DELETE CASCADE
    )
    """)
    
    # 3. Courses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        instructor TEXT,
        capacity INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 4. Enrollments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id TEXT PRIMARY KEY,
        student_email TEXT NOT NULL,
        course_id TEXT NOT NULL,
        status TEXT NOT NULL, -- 'Registered', 'Cancelled'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_email) REFERENCES students(email) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
    )
    """)
    
    # 5. Admin Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        email TEXT PRIMARY KEY,
        password TEXT DEFAULT 'dy6400580'
    )
    """)

    # 6. Email Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id TEXT PRIMARY KEY,
        student_email TEXT NOT NULL,
        student_name TEXT NOT NULL,
        course_name TEXT NOT NULL,
        status TEXT NOT NULL, -- 'Pending', 'Sent', 'Failed'
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        error_message TEXT
    )
    """)
    
    # Run migrations for existing databases
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN password TEXT DEFAULT 'dy6400580'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN password TEXT DEFAULT 'dy6400580'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    conn.commit()
    conn.close()
    
    # Seed initial data
    seed_data()

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if admin exists, if not seed it
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO admin_users (email) VALUES ('parkminah@daeyang.hs.kr')")
        print("Seeded admin user: parkminah@daeyang.hs.kr")
    else:
        cursor.execute("INSERT OR IGNORE INTO admin_users (email) VALUES ('parkminah@daeyang.hs.kr')")
        
        
    # Check if courses exist, if not seed it
    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] == 0:
        initial_courses = [
            ("e스포츠 코스", "김교사", 5, "e스포츠 산업 및 게임 실무 교육"),
            ("IT네트워크 코스", "이교사", 5, "네트워크 설계 및 서버 인프라 관리"),
            ("전자코스", "박교사", 5, "아두이노, 임베디드 및 회로 설계 실습"),
            ("전기코스", "최교사", 5, "전기 설비 및 자동화 제어 실무")
        ]
        for name, instructor, cap, desc in initial_courses:
            c_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO courses (id, name, instructor, capacity, description) VALUES (?, ?, ?, ?, ?)", 
                           (c_id, name, instructor, cap, desc))
        print("Seeded 4 default courses.")
        
    # Check if students exist, if not seed them
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        # We will create 8 mock students with different attendance records
        students_data = [
            # (email, name, grade, class, number, unexcused_abs, unexcused_tard, sick_abs, sick_tard, sick_early)
            ("student1@daeyang.hs.kr", "김철수", 1, 1, 1, 0, 0, 0, 0, 0), # Perfect: 0 points
            ("student2@daeyang.hs.kr", "이영희", 1, 1, 2, 0, 1, 0, 0, 0), # 1 unexcused tardiness: -3 points
            ("student3@daeyang.hs.kr", "박민수", 1, 1, 3, 1, 0, 0, 0, 0), # 1 unexcused absence: -5 points
            ("student4@daeyang.hs.kr", "정수민", 1, 1, 4, 0, 0, 1, 0, 0), # 0 points, 1 sick absence
            ("student5@daeyang.hs.kr", "최준호", 1, 1, 5, 0, 0, 0, 2, 0), # 0 points, 2 sick tardiness
            ("student6@daeyang.hs.kr", "강다은", 1, 1, 6, 0, 0, 0, 0, 1), # 0 points, 1 sick early leave
            ("student7@daeyang.hs.kr", "윤지민", 1, 1, 7, 1, 1, 0, 0, 0), # -8 points
            ("student8@daeyang.hs.kr", "한지우", 1, 1, 8, 0, 0, 0, 0, 0), # Perfect: 0 points
        ]
        
        for email, name, g, c, n, un_abs, un_tard, sk_abs, sk_tard, sk_early in students_data:
            cursor.execute("INSERT OR IGNORE INTO students (email, name, grade, class, number) VALUES (?, ?, ?, ?, ?)",
                           (email, name, g, c, n))
            cursor.execute("""
            INSERT OR IGNORE INTO attendance_records 
            (student_email, unexcused_absences, unexcused_tardiness, sick_absences, sick_tardiness, sick_early_leaves)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (email, un_abs, un_tard, sk_abs, sk_tard, sk_early))
            
        print("Seeded 8 mock students with attendance records.")
        
    conn.commit()
    conn.close()

# Helper queries
def get_courses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_course_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_course_capacity(course_id, capacity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE courses SET capacity = ? WHERE id = ?", (capacity, course_id))
    conn.commit()
    conn.close()

def get_student(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, 
               a.unexcused_absences, a.unexcused_tardiness, 
               a.sick_absences, a.sick_tardiness, a.sick_early_leaves
        FROM students s
        LEFT JOIN attendance_records a ON s.email = a.student_email
        WHERE s.email = ?
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def is_admin(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admin_users WHERE email = ?", (email,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def add_student(email, name, grade, class_num, number, attendance_dict=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO students (email, name, grade, class, number) VALUES (?, ?, ?, ?, ?)",
                       (email, name, grade, class_num, number))
        if attendance_dict is None:
            attendance_dict = {}
        
        cursor.execute("""
            INSERT OR REPLACE INTO attendance_records 
            (student_email, unexcused_absences, unexcused_tardiness, sick_absences, sick_tardiness, sick_early_leaves)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            email,
            attendance_dict.get("unexcused_absences", 0),
            attendance_dict.get("unexcused_tardiness", 0),
            attendance_dict.get("sick_absences", 0),
            attendance_dict.get("sick_tardiness", 0),
            attendance_dict.get("sick_early_leaves", 0)
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding student: {e}")
        return False
    finally:
        conn.close()

def get_enrollments_by_course(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, s.name as student_name, s.grade, s.class, s.number,
               a.unexcused_absences, a.unexcused_tardiness, 
               a.sick_absences, a.sick_tardiness, a.sick_early_leaves
        FROM enrollments e
        JOIN students s ON e.student_email = s.email
        LEFT JOIN attendance_records a ON s.email = a.student_email
        WHERE e.course_id = ? AND e.status = 'Registered'
    """, (course_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_student_enrollment(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, c.name as course_name, c.instructor
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_email = ? AND e.status = 'Registered'
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Calculate score: unexcused_absences * -5 + unexcused_tardiness * -3
def calculate_attendance_score(student):
    if not student:
        return 0
    unexcused_abs = student.get("unexcused_absences", 0) or 0
    unexcused_tard = student.get("unexcused_tardiness", 0) or 0
    return (unexcused_abs * -5) + (unexcused_tard * -3)

# Tie-breaker sort key: returns a tuple used for sorting students
# Priority:
# 1. Attendance score (higher is better, i.e. closer to 0)
# 2. Sick absences (fewer is better)
# 3. Sick tardiness (fewer is better)
# 4. Sick early leaves (fewer is better)
# 5. Enrollment time (earlier is better, i.e. older timestamp)
def get_student_sort_key(student_dict):
    score = calculate_attendance_score(student_dict)
    sick_abs = student_dict.get("sick_absences", 0) or 0
    sick_tard = student_dict.get("sick_tardiness", 0) or 0
    sick_early = student_dict.get("sick_early_leaves", 0) or 0
    
    # Standard ascending sort key where larger values mean LOWER priority:
    # - score (lower score = higher penalty -> we want it to sort first/worst. So we use -score. If score is -5, -score is +5. If score is 0, -score is 0.)
    # - sick_abs (larger value = more sick leave = lower priority)
    # - sick_tard (larger value = lower priority)
    # - sick_early (larger value = lower priority)
    # - enrollment_time (later timestamp = larger string = lower priority)
    
    created_at_str = student_dict.get("created_at", "") or ""
    return (-score, sick_abs, sick_tard, sick_early, created_at_str)

def enroll_student(student_email, course_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Check if student already has a registered course
        cursor.execute("SELECT * FROM enrollments WHERE student_email = ? AND status = 'Registered'", (student_email,))
        existing = cursor.fetchone()
        
        existing_course_id = None
        if existing:
            existing_course_id = existing['course_id']
            if existing_course_id == course_id:
                return {"success": False, "message": "이미 이 과목에 등록되어 있습니다."}
            
            # Temporarily cancel the old course registration inside this transaction
            cursor.execute("""
                UPDATE enrollments 
                SET status = 'Cancelled' 
                WHERE student_email = ? AND course_id = ? AND status = 'Registered'
            """, (student_email, existing_course_id))
        
        # 2. Get course info (capacity)
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        course = cursor.fetchone()
        if not course:
            conn.rollback()
            return {"success": False, "message": "존재하지 않는 과목입니다."}
        
        capacity = course['capacity']
        
        # 3. Get currently registered students count for the NEW course
        cursor.execute("SELECT COUNT(*) FROM enrollments WHERE course_id = ? AND status = 'Registered'", (course_id,))
        current_count = cursor.fetchone()[0]
        
        # 4. Fetch the student's details for priority calculations
        cursor.execute("""
            SELECT s.*, 
                   a.unexcused_absences, a.unexcused_tardiness, 
                   a.sick_absences, a.sick_tardiness, a.sick_early_leaves
            FROM students s
            LEFT JOIN attendance_records a ON s.email = a.student_email
            WHERE s.email = ?
        """, (student_email,))
        new_student_row = cursor.fetchone()
        if not new_student_row:
            conn.rollback()
            return {"success": False, "message": "등록되지 않은 학생입니다. 관리자에게 문의해 주세요."}
            
        new_student = dict(new_student_row)
        new_student['student_email'] = new_student['email']
        new_student['created_at'] = datetime.datetime.now().isoformat()
        
        if current_count < capacity:
            # We have space! Insert registration
            enrollment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO enrollments (id, student_email, course_id, status, created_at)
                VALUES (?, ?, ?, 'Registered', CURRENT_TIMESTAMP)
            """, (enrollment_id, student_email, course_id))
            conn.commit()
            return {"success": True, "message": "수강신청 과목이 변경되었습니다." if existing_course_id else "수강신청이 성공적으로 완료되었습니다."}
        
        else:
            # Capacity is full! We need to rank all registered students + the new student
            cursor.execute("""
                SELECT e.student_email, e.created_at, s.name,
                       a.unexcused_absences, a.unexcused_tardiness, 
                       a.sick_absences, a.sick_tardiness, a.sick_early_leaves
                FROM enrollments e
                JOIN students s ON e.student_email = s.email
                LEFT JOIN attendance_records a ON s.email = a.student_email
                WHERE e.course_id = ? AND e.status = 'Registered'
            """, (course_id,))
            registered_students = [dict(r) for r in cursor.fetchall()]
            
            # Combine them
            all_candidates = registered_students + [new_student]
            
            # Sort them: worst student (lowest priority) ends up at the end of the list (index -1)
            all_candidates.sort(key=get_student_sort_key)
            worst_student = all_candidates[-1]
            
            if worst_student['student_email'] == student_email:
                conn.rollback() # Restores the old course registration
                return {
                    "success": False, 
                    "message": "수강 정원이 초과되었으며, 귀하의 출결 점수가 기존 신청자들보다 낮아 변경이 불가능합니다. (기존 신청 과목 유지)"
                }
            
            # Otherwise, the worst student gets kicked out, and the new student gets registered
            kicked_student_email = worst_student['student_email']
            kicked_student_name = worst_student['name']
            
            # Update worst student's enrollment status to 'Cancelled'
            cursor.execute("""
                UPDATE enrollments 
                SET status = 'Cancelled' 
                WHERE student_email = ? AND course_id = ? AND status = 'Registered'
            """, (kicked_student_email, course_id))
            
            # Insert new student's registration
            enrollment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO enrollments (id, student_email, course_id, status, created_at)
                VALUES (?, ?, ?, 'Registered', CURRENT_TIMESTAMP)
            """, (enrollment_id, student_email, course_id))
            
            # Queue an email log
            cursor.execute("""
                INSERT INTO email_logs (id, student_email, student_name, course_name, status, sent_at)
                VALUES (?, ?, ?, ?, 'Pending', CURRENT_TIMESTAMP)
            """, (str(uuid.uuid4()), kicked_student_email, kicked_student_name, course['name']))
            
            conn.commit()
            
            return {
                "success": True, 
                "message": f"수강신청 과목이 성공적으로 변경되었습니다! (출결 조건에 따라 기존의 {kicked_student_name} 학생이 수강 취소 처리되었습니다.)",
                "kicked_student": {
                    "email": kicked_student_email,
                    "name": kicked_student_name,
                    "course_name": course['name']
                }
            }
            
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"데이터베이스 처리 중 오류가 발생했습니다: {str(e)}"}
    finally:
        conn.close()

def cancel_enrollment(student_email, course_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM enrollments 
            WHERE student_email = ? AND course_id = ? AND status = 'Registered'
        """, (student_email, course_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error cancelling enrollment: {e}")
        return False
    finally:
        conn.close()

def force_enroll_student(student_email, course_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Cancel any existing active enrollment for this student
        cursor.execute("""
            UPDATE enrollments 
            SET status = 'Cancelled' 
            WHERE student_email = ? AND status = 'Registered'
        """, (student_email,))
        
        # Insert forced registration
        enrollment_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO enrollments (id, student_email, course_id, status, created_at)
            VALUES (?, ?, ?, 'Registered', CURRENT_TIMESTAMP)
        """, (enrollment_id, student_email, course_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error in force_enroll_student: {e}")
        return False
    finally:
        conn.close()

def get_email_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM email_logs ORDER BY sent_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_email_status(log_id, status, error_message=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE email_logs 
        SET status = ?, error_message = ? 
        WHERE id = ?
    """, (status, error_message, log_id))
    conn.commit()
    conn.close()

def add_admin(email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO admin_users (email) VALUES (?)", (email,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding admin: {e}")
        return False
    finally:
        conn.close()

def get_unenrolled_students():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.*, 
                   a.unexcused_absences, a.unexcused_tardiness, 
                   a.sick_absences, a.sick_tardiness, a.sick_early_leaves
            FROM students s
            LEFT JOIN attendance_records a ON s.email = a.student_email
            WHERE s.email NOT IN (
                SELECT student_email FROM enrollments WHERE status = 'Registered'
            ) AND s.email NOT IN (SELECT email FROM admin_users)
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error getting unenrolled students: {e}")
        return []
    finally:
        conn.close()

def verify_login(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Check admin_users
        cursor.execute("SELECT * FROM admin_users WHERE email = ?", (email,))
        admin = cursor.fetchone()
        if admin:
            if admin['password'] == password:
                return "admin", dict(admin)
            else:
                return None, "비밀번호가 일치하지 않습니다."
                
        # 2. Check students
        cursor.execute("""
            SELECT s.*, 
                   a.unexcused_absences, a.unexcused_tardiness, 
                   a.sick_absences, a.sick_tardiness, a.sick_early_leaves
            FROM students s
            LEFT JOIN attendance_records a ON s.email = a.student_email
            WHERE s.email = ?
        """, (email,))
        student = cursor.fetchone()
        if student:
            if student['password'] == password:
                return "student", dict(student)
            else:
                return None, "비밀번호가 일치하지 않습니다."
                
        return None, "등록되지 않은 사용자 계정입니다."
    except Exception as e:
        print(f"Error verifying login: {e}")
        return None, f"로그인 처리 중 에러 발생: {str(e)}"
    finally:
        conn.close()

def update_password(email, role, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if role == "admin":
            cursor.execute("UPDATE admin_users SET password = ? WHERE email = ?", (new_password, email))
        else:
            cursor.execute("UPDATE students SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        conn.close()

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.*, 
                   a.unexcused_absences, a.unexcused_tardiness, 
                   a.sick_absences, a.sick_tardiness, a.sick_early_leaves
            FROM students s
            LEFT JOIN attendance_records a ON s.email = a.student_email
            ORDER BY s.grade ASC, s.class ASC, s.number ASC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error getting all students: {e}")
        return []
    finally:
        conn.close()



