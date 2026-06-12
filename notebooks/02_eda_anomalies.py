"""
Deep-dive on data anomalies found in 01_eda.py
Run with: python notebooks/02_eda_anomalies.py
"""
import pandas as pd

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)

RAW = "data/raw"

loyalty = pd.read_csv(f"{RAW}/Customer Loyalty History.csv")
flights = pd.read_csv(f"{RAW}/Customer Flight Activity.csv")

print("### 1. Duplicate (Loyalty Number, Year, Month) rows in flight activity ###")
dupe_mask = flights.duplicated(subset=["Loyalty Number", "Year", "Month"], keep=False)
print("Total duplicated (cust, year, month) rows:", dupe_mask.sum())
sample_id = flights.loc[dupe_mask, "Loyalty Number"].iloc[0]
print(f"\nExample - Loyalty Number {sample_id}, rows for 2017-01:")
print(flights[(flights["Loyalty Number"] == sample_id) & (flights["Year"] == 2017) & (flights["Month"] == 1)])

# Are duplicate rows identical or different values?
g = flights.groupby(["Loyalty Number", "Year", "Month"])
nunique_rows = g.size()
dup_groups = nunique_rows[nunique_rows > 1]
print("\nNumber of (cust, year, month) groups with >1 row:", len(dup_groups))
# check if values are identical within duplicated groups
sample_dup_keys = dup_groups.index[:3]
for key in sample_dup_keys:
    sub = flights[(flights["Loyalty Number"] == key[0]) & (flights["Year"] == key[1]) & (flights["Month"] == key[2])]
    print(f"\nKey {key}:")
    print(sub)

print("\n### 2. Customers with 11 rows - which months are missing? ###")
counts = flights.groupby("Loyalty Number").size()
cust_11 = counts[counts == 11].index[:3]
for cid in cust_11:
    sub = flights[flights["Loyalty Number"] == cid].sort_values(["Year", "Month"])
    months_present = set(zip(sub["Year"], sub["Month"]))
    print(f"\nCustomer {cid}: {sorted(months_present)}")
    cust_row = loyalty[loyalty["Loyalty Number"] == cid]
    print(cust_row[["Enrollment Year", "Enrollment Month", "Cancellation Year", "Cancellation Month"]])

print("\n### 3. Negative salary records ###")
neg_sal = loyalty[loyalty["Salary"] < 0]
print(neg_sal[["Loyalty Number", "Education", "Salary", "Marital Status", "Loyalty Card"]])

print("\n### 4. Missing salary - correlation with Education ###")
print(pd.crosstab(loyalty["Education"], loyalty["Salary"].isna()))

print("\n### 5. Cancellation timing vs flight activity - do cancelled members show 0 flights after cancellation? ###")
cancelled = loyalty[loyalty["Cancellation Year"].notna()].copy()
print("Cancelled members:", len(cancelled))
print("Cancellation Year distribution:\n", cancelled["Cancellation Year"].value_counts().sort_index())

# pick a cancelled-in-2017 customer and check their 2017-2018 flight pattern
c2017 = cancelled[cancelled["Cancellation Year"] == 2017]
if len(c2017) > 0:
    cid = c2017["Loyalty Number"].iloc[0]
    crow = c2017[c2017["Loyalty Number"] == cid]
    print(f"\nExample customer {cid}, cancelled {crow['Cancellation Year'].values[0]}-{crow['Cancellation Month'].values[0]}")
    sub = flights[flights["Loyalty Number"] == cid].sort_values(["Year", "Month"])
    print(sub[["Year", "Month", "Total Flights", "Points Accumulated", "Points Redeemed"]].to_string(index=False))

print("\n### 6. Overall: do cancelled members still show flight activity in 2018? ###")
flights_2018 = flights[flights["Year"] == 2018].groupby("Loyalty Number")["Total Flights"].sum()
cancelled_ids = set(loyalty.loc[loyalty["Cancellation Year"].notna(), "Loyalty Number"])
cancelled_2018_activity = flights_2018[flights_2018.index.isin(cancelled_ids)]
print("Cancelled members with >0 flights in 2018:", (cancelled_2018_activity > 0).sum(), "/", len(cancelled_2018_activity))

print("\n### 7. Active (non-cancelled) members with zero flights all of 2018 ###")
active_ids = set(loyalty.loc[loyalty["Cancellation Year"].isna(), "Loyalty Number"])
active_2018_activity = flights_2018[flights_2018.index.isin(active_ids)]
zero_2018 = (active_2018_activity == 0).sum()
print(f"Active members with zero 2018 flights: {zero_2018} / {len(active_2018_activity)} ({zero_2018/len(active_2018_activity)*100:.1f}%)")

print("\n### 8. CLV vs Salary correlation (sanity) ###")
merged = loyalty.dropna(subset=["Salary"])
print("Correlation CLV vs Salary:", merged["CLV"].corr(merged["Salary"]))
