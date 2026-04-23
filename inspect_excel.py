import pandas as pd
import sys
import json

file_path = "2026학년도 신입생 교육과정 편제표_대양고.xlsx"

try:
    with open("excel_info.txt", "w", encoding="utf-8") as f:
        xls = pd.ExcelFile(file_path)
        f.write(f"Sheet Names: {xls.sheet_names}\n\n")
        
        for sheet in xls.sheet_names:
            f.write(f"\n--- Sheet: {sheet} ---\n")
            df = pd.read_excel(xls, sheet_name=sheet, nrows=20)
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            f.write(df.head(20).to_markdown())
            f.write("\n")
except Exception as e:
    with open("excel_info.txt", "w", encoding="utf-8") as f:
        f.write(f"Error reading excel: {e}")
