import streamlit as st
import pandas as pd

st.title("🛠️ 엑셀 파일 분석 디버거")

uploaded_file = st.file_uploader("디버깅할 엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file is not None:
    xls = pd.ExcelFile(uploaded_file)
    st.write("### 📂 시트 목록", xls.sheet_names)
    
    target_sheet = st.selectbox("시트 선택", xls.sheet_names)
    
    if target_sheet:
        df = pd.read_excel(xls, sheet_name=target_sheet, header=None)
        st.write(f"### 📊 '{target_sheet}' 데이터 미리보기 (처음 20줄)")
        st.dataframe(df.head(20))
        
        st.write("### 🔍 파싱 테스트 (8번 행부터)")
        data_df = df.iloc[8:].copy()
        
        test_results = []
        for idx, row in data_df.head(15).iterrows():
            domain = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else "nan"
            name_candidates = [str(row[i]).strip() for i in [6, 5, 4] if i < len(row) and pd.notna(row[i]) and str(row[i]).strip() != "nan"]
            subject_name = name_candidates[0] if name_candidates else "nan"
            test_results.append({
                "Excel Row": idx + 1,
                "Domain (Col B)": domain,
                "Subject Name": subject_name
            })
            
        st.table(test_results)
