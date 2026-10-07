import pandas as pd

file = "data/source/prosandcons.xlsx"

excel = pd.ExcelFile(file)

print("SHEETS:", excel.sheet_names)

for sheet in excel.sheet_names:
    print("\n---", sheet, "---")

    df = pd.read_excel(file, sheet_name=sheet)

    print("SHAPE:", df.shape)
    print("COLUMNS:", list(df.columns))
    print("\nSAMPLE:")
    print(df.head(10).to_string(index=False))