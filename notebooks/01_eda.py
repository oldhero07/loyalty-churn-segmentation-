"""
Initial EDA for PS3 - Airline Loyalty Program
Run with: python notebooks/01_eda.py
"""
import pandas as pd

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)

RAW = "data/raw"

loyalty = pd.read_csv(f"{RAW}/Customer Loyalty History.csv")
flights = pd.read_csv(f"{RAW}/Customer Flight Activity.csv")
calendar = pd.read_csv(f"{RAW}/Calendar.csv")

print("=" * 70)
print("CUSTOMER LOYALTY HISTORY")
print("=" * 70)
print("Shape:", loyalty.shape)
print(loyalty.dtypes)
print("\nMissing values:\n", loyalty.isna().sum())
print("\nDuplicate Loyalty Numbers:", loyalty["Loyalty Number"].duplicated().sum())

print("\n-- Categorical value counts --")
for col in ["Country", "Province", "Gender", "Education", "Marital Status", "Loyalty Card", "Enrollment Type"]:
    print(f"\n{col}:")
    print(loyalty[col].value_counts(dropna=False))

print("\n-- Numeric describe --")
print(loyalty[["Salary", "CLV", "Enrollment Year", "Enrollment Month", "Cancellation Year", "Cancellation Month"]].describe())

print("\nNegative salaries:", (loyalty["Salary"] < 0).sum())
print("Cancelled members:", loyalty["Cancellation Year"].notna().sum())
print("Enrollment Year range:", loyalty["Enrollment Year"].min(), "-", loyalty["Enrollment Year"].max())
print("Enrollment Type counts:\n", loyalty["Enrollment Type"].value_counts())

print("\n" + "=" * 70)
print("CUSTOMER FLIGHT ACTIVITY")
print("=" * 70)
print("Shape:", flights.shape)
print(flights.dtypes)
print("\nMissing values:\n", flights.isna().sum())
print("\nYear range:", flights["Year"].min(), "-", flights["Year"].max())
print("Month range:", flights["Month"].min(), "-", flights["Month"].max())
print("\nUnique Loyalty Numbers in flights:", flights["Loyalty Number"].nunique())
print("Unique Loyalty Numbers in loyalty history:", loyalty["Loyalty Number"].nunique())
print("Loyalty numbers in flights but not in history:",
      len(set(flights["Loyalty Number"]) - set(loyalty["Loyalty Number"])))
print("Loyalty numbers in history but not in flights:",
      len(set(loyalty["Loyalty Number"]) - set(flights["Loyalty Number"])))

print("\nRows per customer (should be 84 for 7 years x 12 months):")
rows_per_cust = flights.groupby("Loyalty Number").size()
print(rows_per_cust.describe())
print(rows_per_cust.value_counts().head())

print("\n-- Numeric describe --")
print(flights[["Total Flights", "Distance", "Points Accumulated", "Points Redeemed", "Dollar Cost Points Redeemed"]].describe())

print("\nNegative values check:")
for col in ["Total Flights", "Distance", "Points Accumulated", "Points Redeemed", "Dollar Cost Points Redeemed"]:
    print(f"  {col}: negatives = {(flights[col] < 0).sum()}")

print("\nRows with 0 flights but nonzero distance/points:")
zero_flight = flights[flights["Total Flights"] == 0]
print("  Zero-flight rows:", len(zero_flight))
print("  ...with distance > 0:", (zero_flight["Distance"] > 0).sum())
print("  ...with points accumulated > 0:", (zero_flight["Points Accumulated"] > 0).sum())
print("  ...with points redeemed > 0:", (zero_flight["Points Redeemed"] > 0).sum())

print("\nRedeemed > Accumulated (cumulative check skipped, per-row):")
print((flights["Points Redeemed"] > flights["Points Accumulated"]).sum())

print("\n" + "=" * 70)
print("CALENDAR")
print("=" * 70)
print("Shape:", calendar.shape)
print(calendar.head())
print("Date range:", calendar["Date"].min(), "-", calendar["Date"].max())
