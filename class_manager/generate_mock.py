import pandas as pd
import random

def generate_mock_excel(filename="mock_students.xlsx", num_students=30):
    # Names for random generation
    last_names = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '전', '홍']
    first_names_m = ['민준', '서준', '도윤', '예준', '시우', '하준', '주원', '지호', '지훈', '준우', '건우', '우진', '선우', '서진', '연우', '은우', '윤우', '승우', '시윤', '지환']
    first_names_f = ['서아', '지안', '하윤', '서윤', '하은', '지우', '수아', '지민', '윤서', '채원', '예린', '은서', '소율', '시은', '다은', '지아', '서연', '유진', '수빈', '유나']
    
    data = []
    
    # Let's say it's 1st grade, Class 1
    grade = 1
    class_num = 1
    
    for i in range(1, num_students + 1):
        # 50/50 chance for male/female
        gender = '남' if random.random() > 0.5 else '여'
        
        last_name = random.choice(last_names)
        if gender == '남':
            first_name = random.choice(first_names_m)
        else:
            first_name = random.choice(first_names_f)
            
        full_name = last_name + first_name
        
        # Student ID format: Grade(1) Class(2) Num(2) => 10101
        student_id = int(f"{grade}{class_num:02d}{i:02d}")
        
        # Random score between 50 and 100
        score = random.randint(50, 100)
        
        data.append({
            '학년': grade,
            '학번': student_id,
            '이름': full_name,
            '성별': gender,
            '성적': score
        })
        
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Success! {filename} generated (total {num_students} students)")

if __name__ == "__main__":
    generate_mock_excel()
