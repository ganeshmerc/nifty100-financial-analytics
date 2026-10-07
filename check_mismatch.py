import pandas as pd

companies = pd.read_excel("data/source/companies.xlsx", header=1)
companies_ids = set(companies["id"].astype(str).str.strip())

pnl = pd.read_excel("data/source/profitandloss.xlsx", header=1)
pnl_ids = set(pnl["company_id"].astype(str).str.strip())

missing = pnl_ids - companies_ids

print("Company IDs in profitandloss but NOT in companies:")
print(sorted(missing))
print(f"\nTotal missing: {len(missing)}")
print(f"Total unique IDs in profitandloss: {len(pnl_ids)}")
print(f"Total unique IDs in companies: {len(companies_ids)}")