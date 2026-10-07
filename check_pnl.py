import pandas as pd

df = pd.read_excel("data/source/profitandloss.xlsx", header=1)
print(list(df.columns))
print(df[["company_id"]].head(5))
print(df["company_id"].dtype)