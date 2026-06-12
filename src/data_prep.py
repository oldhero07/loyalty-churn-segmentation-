"""
Data loading & cleaning for the Airline Loyalty Program dataset.

Cleaning decisions are documented in reports/supporting_analysis/data_quality_notes.md:
  1. Drop exact full-row duplicates in flight activity.
  2. Aggregate (sum) remaining same (Loyalty Number, Year, Month) rows.
  3. Fix sign-error negative salaries (abs value).
  4. Add a `salary_missing` flag (College segment is MNAR for salary) -
     do not blanket-impute with a population statistic.
"""
import pandas as pd

RAW_DIR = "data/raw"


def load_raw():
    loyalty = pd.read_csv(f"{RAW_DIR}/Customer Loyalty History.csv")
    flights = pd.read_csv(f"{RAW_DIR}/Customer Flight Activity.csv")
    calendar = pd.read_csv(f"{RAW_DIR}/Calendar.csv", parse_dates=["Date", "Start of Year", "Start of Quarter", "Start of Month"])
    return loyalty, flights, calendar


def clean_flights(flights: pd.DataFrame) -> pd.DataFrame:
    df = flights.copy()

    # 1. Drop exact full-row duplicates
    df = df.drop_duplicates()

    # 2. Aggregate remaining (cust, year, month) duplicates by summing numeric cols
    numeric_cols = ["Total Flights", "Distance", "Points Accumulated",
                     "Points Redeemed", "Dollar Cost Points Redeemed"]
    df = (
        df.groupby(["Loyalty Number", "Year", "Month"], as_index=False)[numeric_cols]
        .sum()
    )

    df["period"] = pd.to_datetime(dict(year=df["Year"], month=df["Month"], day=1))
    return df


def clean_loyalty(loyalty: pd.DataFrame) -> pd.DataFrame:
    df = loyalty.copy()

    # 3. Fix sign-error negative salaries
    df["Salary"] = df["Salary"].abs()

    # 4. Missing-salary flag (MNAR, concentrated in College education)
    df["salary_missing"] = df["Salary"].isna().astype(int)

    df["is_cancelled"] = df["Cancellation Year"].notna().astype(int)

    # Tenure as of end of 2017 (years since enrollment), used for observation-window features
    df["enrollment_date"] = pd.to_datetime(
        dict(year=df["Enrollment Year"], month=df["Enrollment Month"], day=1)
    )
    df["cancellation_date"] = pd.to_datetime(
        {"year": df["Cancellation Year"], "month": df["Cancellation Month"], "day": 1},
        errors="coerce",
    )

    return df


def get_clean_data():
    loyalty, flights, calendar = load_raw()
    loyalty_clean = clean_loyalty(loyalty)
    flights_clean = clean_flights(flights)
    return loyalty_clean, flights_clean, calendar


if __name__ == "__main__":
    loyalty_clean, flights_clean, calendar = get_clean_data()
    print("Loyalty clean shape:", loyalty_clean.shape)
    print("Flights clean shape:", flights_clean.shape)
    loyalty_clean.to_csv("data/processed/loyalty_clean.csv", index=False)
    flights_clean.to_csv("data/processed/flights_clean.csv", index=False)
    print("Saved to data/processed/")
