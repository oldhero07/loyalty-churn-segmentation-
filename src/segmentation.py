"""
Customer segmentation & value analysis.

Goal: go beyond static CLV. Combine behavioral signals (2017 engagement,
recency, redemption, momentum), tenure, and the churn-risk score from
churn_model.py with demographics to build segments that are:
  - meaningfully distinct (different value/risk profiles)
  - actionable (map to a specific retention/marketing motion)

Note: segmentation runs on the "at risk entering 2018" cohort (in_cohort==1,
15,315 members) - i.e. the same population used for churn modeling. Members
already cancelled on/before 2017 (1,422 members) are guaranteed
blended_churn==1 by construction (they left before the observation window
even ends) and have no churn_risk_score; including them would distort every
segment's "actual churn rate" and "avg churn risk" by the share of these
already-departed members it happens to contain.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


CLUSTER_FEATURES = [
    "CLV", "total_flights", "pct_months_active", "recency_months",
    "redemption_rate", "tenure_years", "momentum",
]


def load_data():
    df = pd.read_csv("data/processed/model_dataset.csv")
    df = df[df["in_cohort"] == 1].copy()
    scores = pd.read_csv("data/processed/churn_scores.csv")[["Loyalty Number", "churn_risk_score"]]
    df = df.merge(scores, on="Loyalty Number", how="left")
    return df


def choose_k(X_scaled, k_range=range(3, 8)):
    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        results.append((k, sil, km.inertia_))
        print(f"k={k}: silhouette={sil:.3f}, inertia={km.inertia_:.0f}")
    return results


def main():
    df = load_data()

    X = df[CLUSTER_FEATURES].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("=== Choosing k ===")
    choose_k(X_scaled)

    K = 5
    km = KMeans(n_clusters=K, random_state=42, n_init=10)
    df["segment"] = km.fit_predict(X_scaled)

    print(f"\n=== Segment profiles (k={K}) ===")
    profile = df.groupby("segment").agg(
        n=("Loyalty Number", "size"),
        clv_mean=("CLV", "mean"),
        total_flights_mean=("total_flights", "mean"),
        pct_months_active_mean=("pct_months_active", "mean"),
        recency_months_mean=("recency_months", "mean"),
        redemption_rate_mean=("redemption_rate", "mean"),
        tenure_years_mean=("tenure_years", "mean"),
        momentum_mean=("momentum", "mean"),
        churn_risk_mean=("churn_risk_score", "mean"),
        salary_mean=("Salary", "mean"),
    ).round(2)
    print(profile.to_string())

    print("\n=== Loyalty Card distribution by segment ===")
    print(pd.crosstab(df["segment"], df["Loyalty Card"], normalize="index").round(2))

    print("\n=== Education distribution by segment ===")
    print(pd.crosstab(df["segment"], df["Education"], normalize="index").round(2))

    print("\n=== was_active_2017 / blended_churn rate by segment ===")
    print(df.groupby("segment")[["was_active_2017", "blended_churn"]].mean().round(3))

    # NOTE: cluster IDs are not stable across re-runs (KMeans labels are
    # arbitrary) - this mapping must be checked against the printed segment
    # profile each time (CLV, momentum, tenure, recency identify each group).
    segment_names = {
        0: "VIP Loyalists",
        1: "Dormant / Lapsed",
        2: "New / Onboarding",
        3: "Cooling Loyalists",
        4: "Growing Loyalists",
    }
    df["segment_name"] = df["segment"].map(segment_names)

    df.to_csv("data/processed/segmented_customers.csv", index=False)
    profile.to_csv("data/processed/segment_profiles.csv")
    print("\nSaved segmented_customers.csv and segment_profiles.csv")
    print("\nSegment sizes:")
    print(df["segment_name"].value_counts())


if __name__ == "__main__":
    main()
