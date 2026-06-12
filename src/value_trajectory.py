"""
Value Trajectory framework -- answers PS3's explicit question:
  "The business already tracks CLV. Is that metric telling the full story?
   What makes a customer genuinely valuable, not just historically, but
   going forward?"

An earlier version of this analysis paired CLV with `momentum` (H2-H1 2017
flight trend) and found that a "decelerating high-value" group churned at
~2x the rate of an "accelerating" one. That turned out to be an artifact of
including 1,422 members already cancelled on/before 2017 (guaranteed
blended_churn==1 by construction) in the analysis population. On the
corrected "at risk entering 2018" population (in_cohort==1, 15,315 members -
see segmentation.py), the correlation between momentum and blended_churn is
essentially zero (r ~= -0.013) and the earlier finding does not hold.

What DOES hold up: CLV is essentially independent of the churn-risk score
(r ~= 0.01) -- and the churn-risk score IS reasonably calibrated to actual
churn for the engaged population (see reports/supporting_analysis/churn_model_summary.md, AUC 0.65).
So the honest "is CLV telling the full story" answer is: CLV tells you
nothing about risk, and the model's risk score does -- pairing the two
surfaces high-CLV members the model flags as elevated-risk, which a
CLV-only report would never see.

Quadrants (CLV top-tercile = "High CLV", churn_risk_score top-quartile =
"Elevated Risk"):
  - At-Risk High Value : High CLV, Elevated Risk  -> highest-priority save
  - Protected Core     : High CLV, Lower Risk     -> protect & reward
  - Win-Back Priority  : Low/Mid CLV, Elevated Risk -> cost-effective win-back
  - Steady Base        : Low/Mid CLV, Lower Risk  -> low-cost monitoring
"""
import pandas as pd


def main():
    df = pd.read_csv("data/processed/segmented_customers.csv")
    df = df.drop(columns=["clv_tier", "trajectory", "value_quadrant"], errors="ignore")

    # --- Document the momentum finding before moving on ---
    print("=== Correlation check (why momentum was dropped from this framework) ===")
    print(f"corr(momentum, blended_churn)      = {df['momentum'].corr(df['blended_churn']):.3f}")
    print(f"corr(CLV, churn_risk_score)        = {df['CLV'].corr(df['churn_risk_score']):.3f}")
    print(f"corr(CLV, blended_churn)           = {df['CLV'].corr(df['blended_churn']):.3f}")
    print(f"corr(recency_months, blended_churn)= {df['recency_months'].corr(df['blended_churn']):.3f}")

    clv_high_cutoff = df["CLV"].quantile(2 / 3)
    risk_high_cutoff = df["churn_risk_score"].quantile(0.75)

    df["clv_tier"] = (df["CLV"] >= clv_high_cutoff).map({True: "High CLV", False: "Low/Mid CLV"})
    df["risk_tier"] = (df["churn_risk_score"] >= risk_high_cutoff).map(
        {True: "Elevated Risk", False: "Lower Risk"}
    )

    quadrant_map = {
        ("High CLV", "Elevated Risk"): "At-Risk High Value",
        ("High CLV", "Lower Risk"): "Protected Core",
        ("Low/Mid CLV", "Elevated Risk"): "Win-Back Priority",
        ("Low/Mid CLV", "Lower Risk"): "Steady Base",
    }
    df["value_quadrant"] = df.apply(lambda r: quadrant_map[(r["clv_tier"], r["risk_tier"])], axis=1)

    print(f"\nHigh-CLV cutoff (top tercile): ${clv_high_cutoff:,.2f}")
    print(f"Elevated-risk cutoff (top quartile of churn_risk_score): {risk_high_cutoff:.3f}")

    print("\n=== Quadrant sizes & profile ===")
    profile = df.groupby("value_quadrant").agg(
        n=("Loyalty Number", "size"),
        clv_mean=("CLV", "mean"),
        clv_sum=("CLV", "sum"),
        churn_risk_mean=("churn_risk_score", "mean"),
        blended_churn_rate=("blended_churn", "mean"),
        recency_months_mean=("recency_months", "mean"),
    ).round(3)
    print(profile.to_string())

    print("\n=== Quadrant x behavioral segment crosstab (counts) ===")
    print(pd.crosstab(df["value_quadrant"], df["segment_name"]).to_string())

    arhv = df[df["value_quadrant"] == "At-Risk High Value"]
    print(f"\nAt-Risk High Value: {len(arhv)} members, "
          f"total CLV = ${arhv['CLV'].sum():,.0f}, "
          f"avg churn risk score = {arhv['churn_risk_score'].mean():.3f}, "
          f"actual blended churn rate = {arhv['blended_churn'].mean():.3f}")

    df.to_csv("data/processed/segmented_customers.csv", index=False)
    profile.to_csv("data/processed/value_quadrant_profiles.csv")
    print("\nUpdated segmented_customers.csv with value_quadrant; saved value_quadrant_profiles.csv")


if __name__ == "__main__":
    main()
