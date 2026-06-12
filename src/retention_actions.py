"""
Maps each member to a retention-playbook action group (reports/supporting_analysis/retention_playbook.md).

Priority order matters: a member could technically match multiple rules; the
first matching rule below wins, reflecting the playbook's stated priority
order. Groups are defined by (a) tenure status (new vs. established) and then
(b) the CLV x churn-risk value_quadrant from value_trajectory.py, with VIP
membership as a tie-breaker for tone/channel (white-glove vs. automated).
"""
import pandas as pd


def assign_action(row):
    seg = row["segment_name"]
    quad = row["value_quadrant"]
    is_vip = seg == "VIP Loyalists"

    if row["in_training_cohort"] == 0:
        return (
            "New / Onboarding journey",
            "Welcome series + first-flight bonus + 30/90-day check-ins",
            "Always-on (from enrollment)",
            "% completing 1 flight + 1 redemption in 6 months",
        )

    if quad == "At-Risk High Value" and is_vip:
        return (
            "VIP win-back (urgent)",
            "Personal relationship-desk call + tier-hold guarantee + bonus-mile offer",
            "Within 2 weeks (manual queue)",
            "Reactivation rate within 90 days",
        )

    if quad == "At-Risk High Value":
        return (
            "High-value win-back",
            "Personalized win-back offer (bonus miles tied to past travel pattern) + "
            "proactive outreach",
            "Triggered at next quarterly refresh",
            "Re-activation rate within 60 days vs. control",
        )

    if quad == "Win-Back Priority":
        return (
            "Standard reactivation",
            "3-email automated win-back series over 6 weeks",
            "Triggered on entering this group",
            "Reactivation rate (any flight in 6 months)",
        )

    if quad == "Protected Core" and is_vip:
        return (
            "VIP recognition",
            "Tier-anniversary perks, lounge passes, early redemption access",
            "Always-on (milestone-triggered)",
            "YoY CLV growth, churn risk stays low at next refresh",
        )

    if quad == "Protected Core":
        return (
            "Nurture toward VIP",
            "Tier-progress nudges + partner offers + redemption prompts",
            "Always-on (milestone-triggered)",
            "Tier-upgrade rate within 12 months",
        )

    return (
        "Light-touch monitoring",
        "Automated quarterly redemption reminder / seasonal promo",
        "Quarterly batch",
        "Open/click-through rate, incremental bookings vs. control",
    )


def main():
    df = pd.read_csv("data/processed/segmented_customers.csv")
    df = df.drop(columns=["action_group", "recommended_action", "timing", "success_metric"],
                  errors="ignore")

    actions = df.apply(assign_action, axis=1, result_type="expand")
    actions.columns = ["action_group", "recommended_action", "timing", "success_metric"]
    df = pd.concat([df, actions], axis=1)

    print("=== Action group sizes & CLV ===")
    print(df.groupby("action_group").agg(
        members=("Loyalty Number", "size"),
        total_clv=("CLV", "sum"),
        avg_churn_risk=("churn_risk_score", "mean"),
        actual_churn_rate=("blended_churn", "mean"),
    ).round(3).to_string())

    df.to_csv("data/processed/segmented_customers.csv", index=False)
    print("\nUpdated segmented_customers.csv with action_group / recommended_action / timing / success_metric")


if __name__ == "__main__":
    main()
