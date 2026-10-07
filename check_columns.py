import pandas as pd

df = pd.read_excel("data/source/companies.xlsx", header=1)
print(list(df.columns))
print(df.head(3))