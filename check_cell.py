import pandas as pd
xls = pd.ExcelFile('c:/Users/User/dev/tutorial/2026학년도 신입생 교육과정 편제표_대양고.xlsx')
sheet_name = '실무과목 능력단위(e스포츠과)'
df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
with open('cell_value.txt', 'w', encoding='utf-8') as f:
    f.write(str(df.iloc[29, 1]))
