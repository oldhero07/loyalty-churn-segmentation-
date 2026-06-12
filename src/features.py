"""
Feature engineering & churn-label construction.

Design (documented fully in reports/supporting_analysis/churn_definition.md):
  - OBSERVATION window = 2017 (Jan-Dec) -> all predictive features.
  - OUTCOME window     = 2018 (Jan-Dec) -> churn labels only.
  - Cohort = customers who were "at risk" entering 2018, i.e. NOT already
    cancelled on/before 2017-12-31. This avoids leakage: nothing from 2018
    is used as a feature, and customers already churned before the
    observation window ends are excluded from the prediction task.
"""
import numpy as np
import pandas as pd

from data_prep import get_clean_data

OBS_YEAR = 2017
OUTCOME_YEAR = 2018


def _monthly_pivot(flights_clean, year, value_col):
    sub = flights_clean[flights_clean["Year"] == year]
    pivot = sub.pivot_table(index="Loyalty Number", columns="Month", values=value_col, fill_value=0)
    pivot = pivot.reindex(columns=range(1, 13), fill_value=0)
    return pivot


def build_observation_features(flights_clean: pd.DataFrame, loyalty_clean: pd.DataFrame,
                                obs_year: int = OBS_YEAR) -> pd.DataFrame:
    flights_pivot = _monthly_pivot(flights_clean, obs_year, "Total Flights")
    points_acc_pivot = _monthly_pivot(flights_clean, obs_year, "Points Accumulated")
    points_red_pivot = _monthly_pivot(flights_clean, obs_year, "Points Redeemed")
    dollar_red_pivot = _monthly_pivot(flights_clean, obs_year, "Dollar Cost Points Redeemed")
    distance_pivot = _monthly_pivot(flights_clean, obs_year, "Distance")

    feats = pd.DataFrame(index=flights_pivot.index)
    feats["total_flights"] = flights_pivot.sum(axis=1)
    feats["total_distance"] = distance_pivot.sum(axis=1)
    feats["total_points_accumulated"] = points_acc_pivot.sum(axis=1)
    feats["total_points_redeemed"] = points_red_pivot.sum(axis=1)
    feats["total_dollar_redeemed"] = dollar_red_pivot.sum(axis=1)

    active_mask = flights_pivot > 0
    feats["active_months"] = active_mask.sum(axis=1)
    feats["pct_months_active"] = feats["active_months"] / 12.0
    feats["avg_flights_per_active_month"] = (
        feats["total_flights"] / feats["active_months"].replace(0, np.nan)
    ).fillna(0)
    feats["flight_volatility"] = flights_pivot.std(axis=1)

    # Redemption behaviour
    feats["redemption_rate"] = (
        feats["total_points_redeemed"] / feats["total_points_accumulated"].replace(0, np.nan)
    ).fillna(0).clip(0, 1)
    feats["has_redeemed"] = (feats["total_points_redeemed"] > 0).astype(int)

    # Recency: months since last active month within the observation year
    # (0 = active in December, 12 = no activity at all in the year)
    last_active_month = active_mask.apply(
        lambda row: row[row].index.max() if row.any() else 0, axis=1
    )
    feats["recency_months"] = 12 - last_active_month

    # Momentum: H2 vs H1 activity (deceleration / acceleration)
    h1 = flights_pivot[[1, 2, 3, 4, 5, 6]].sum(axis=1)
    h2 = flights_pivot[[7, 8, 9, 10, 11, 12]].sum(axis=1)
    feats["h1_flights"] = h1
    feats["h2_flights"] = h2
    feats["momentum"] = h2 - h1  # negative => decelerating engagement

    # Redemption trend: is the member starting to cash in points more (H2 vs H1)?
    h1_redeemed = points_red_pivot[[1, 2, 3, 4, 5, 6]].sum(axis=1)
    h2_redeemed = points_red_pivot[[7, 8, 9, 10, 11, 12]].sum(axis=1)
    feats["redemption_momentum"] = h2_redeemed - h1_redeemed

    # Distance per flight: proxy for trip length / fare class (long-haul vs short-hop flyer)
    feats["distance_per_flight"] = (
        feats["total_distance"] / feats["total_flights"].replace(0, np.nan)
    ).fillna(0)

    feats = feats.reset_index()

    # Demographics & account attributes (point-in-time, non-leaking)
    demo_cols = ["Loyalty Number", "Country", "Province", "City", "Gender", "Education",
                  "Salary", "salary_missing", "Marital Status", "Loyalty Card", "CLV",
                  "Enrollment Type", "Enrollment Year", "Enrollment Month"]
    demo = loyalty_clean[demo_cols].copy()

    cutoff = pd.Timestamp(f"{obs_year}-12-31")
    enrollment_date = pd.to_datetime(
        dict(year=demo["Enrollment Year"], month=demo["Enrollment Month"], day=1)
    )
    demo["tenure_years"] = ((cutoff - enrollment_date).dt.days / 365.25).clip(lower=0)

    out = demo.merge(feats, on="Loyalty Number", how="left")
    # customers with no rows at all in the observation year -> all-zero engagement
    fill_cols = [c for c in feats.columns if c != "Loyalty Number"]
    out[fill_cols] = out[fill_cols].fillna(0)

    return out


def build_churn_labels(flights_clean: pd.DataFrame, loyalty_clean: pd.DataFrame,
                        outcome_year: int = OUTCOME_YEAR) -> pd.DataFrame:
    flights_outcome = (
        flights_clean[flights_clean["Year"] == outcome_year]
        .groupby("Loyalty Number")["Total Flights"].sum()
        .rename("total_flights_outcome")
    )

    df = loyalty_clean[["Loyalty Number", "Cancellation Year"]].merge(
        flights_outcome, on="Loyalty Number", how="left"
    )
    df["total_flights_outcome"] = df["total_flights_outcome"].fillna(0)

    df["hard_churn"] = (df["Cancellation Year"] == outcome_year).astype(int)
    df["behavioral_churn"] = (df["total_flights_outcome"] == 0).astype(int)
    df["blended_churn"] = ((df["hard_churn"] == 1) | (df["behavioral_churn"] == 1)).astype(int)

    return df[["Loyalty Number", "hard_churn", "behavioral_churn", "blended_churn", "total_flights_outcome"]]


def build_modeling_cohort(loyalty_clean: pd.DataFrame) -> pd.Series:
    """Scoring cohort: 'at risk' entering the outcome year, i.e. not already
    cancelled by end of the observation year. Used for segmentation/dashboard
    scoring (broad population)."""
    already_cancelled = (
        loyalty_clean["Cancellation Year"].notna()
        & (loyalty_clean["Cancellation Year"] <= OBS_YEAR)
    )
    cohort = loyalty_clean.loc[~already_cancelled, "Loyalty Number"]
    return cohort


def build_training_cohort(loyalty_clean: pd.DataFrame) -> pd.Series:
    """Training/evaluation cohort: members who (a) were not already cancelled
    by end of the observation year, AND (b) were enrolled on/before the
    observation year, so a full 12-month observation history exists.

    Members enrolled in OUTCOME_YEAR (2018) have zero 2017 history by
    definition (tenure_years == 0, all activity features == 0) - including
    them in training would let the model learn a trivial "tenure==0 -> new
    member -> higher churn" rule rather than a behavioral pattern, and
    conflates "new member churn" with "established member churn" (3,010
    members, 18.1% blended-churn rate vs 6.2% for established members).
    They are still SCORED (via build_modeling_cohort) and handled separately
    in segmentation as the New/Onboarding segment.
    """
    already_cancelled = (
        loyalty_clean["Cancellation Year"].notna()
        & (loyalty_clean["Cancellation Year"] <= OBS_YEAR)
    )
    not_yet_enrolled = loyalty_clean["Enrollment Year"] > OBS_YEAR
    cohort = loyalty_clean.loc[~already_cancelled & ~not_yet_enrolled, "Loyalty Number"]
    return cohort


def build_dataset():
    loyalty_clean, flights_clean, _ = get_clean_data()

    features = build_observation_features(flights_clean, loyalty_clean)
    labels = build_churn_labels(flights_clean, loyalty_clean)
    cohort = build_modeling_cohort(loyalty_clean)

    training_cohort = build_training_cohort(loyalty_clean)

    dataset = features.merge(labels, on="Loyalty Number", how="left")
    dataset["in_cohort"] = dataset["Loyalty Number"].isin(cohort).astype(int)
    dataset["in_training_cohort"] = dataset["Loyalty Number"].isin(training_cohort).astype(int)
    dataset["was_active_2017"] = (dataset["active_months"] > 0).astype(int)

    return dataset


if __name__ == "__main__":
    dataset = build_dataset()
    print("Dataset shape:", dataset.shape)
    print("Cohort size (in_cohort=1):", dataset["in_cohort"].sum())
    cohort_df = dataset[dataset["in_cohort"] == 1]
    print("\nChurn rate (hard):", cohort_df["hard_churn"].mean().round(4))
    print("Churn rate (behavioral):", cohort_df["behavioral_churn"].mean().round(4))
    print("Churn rate (blended):", cohort_df["blended_churn"].mean().round(4))
    print("\nOverlap (hard & behavioral both 1):",
          ((cohort_df["hard_churn"] == 1) & (cohort_df["behavioral_churn"] == 1)).sum())
    print("Hard=1, Behavioral=0:",
          ((cohort_df["hard_churn"] == 1) & (cohort_df["behavioral_churn"] == 0)).sum())
    print("Hard=0, Behavioral=1:",
          ((cohort_df["hard_churn"] == 0) & (cohort_df["behavioral_churn"] == 1)).sum())

    dataset.to_csv("data/processed/model_dataset.csv", index=False)
    print("\nSaved to data/processed/model_dataset.csv")
