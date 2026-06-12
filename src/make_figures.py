"""Generate static figures for the technical report (reports/) from
data/processed/*.csv. Run from the project root: python src/make_figures.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT = "figures"


def fig_feature_importance():
    imp = pd.read_csv("data/processed/feature_importance.csv").head(10)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(imp["feature"][::-1], imp["importance"][::-1], color="#1f77b4")
    ax.set_xlabel("Importance (GBM)")
    ax.set_title("Top 10 churn-model features")
    fig.tight_layout()
    fig.savefig(f"{OUT}/feature_importance.png", dpi=150)
    plt.close(fig)


def fig_value_trajectory():
    df = pd.read_csv("data/processed/segmented_customers.csv")
    colors = {
        "At-Risk High Value": "#d62728",
        "Protected Core": "#2ca02c",
        "Win-Back Priority": "#9467bd",
        "Steady Base": "#7f7f7f",
    }
    fig, ax = plt.subplots(figsize=(7, 5))
    for quad, sub in df.groupby("value_quadrant"):
        ax.scatter(sub["churn_risk_score"], sub["CLV"], s=8, color=colors.get(quad, "gray"),
                   alpha=0.25, label=f"{quad} (n={len(sub):,})")
    ax.axvline(df["churn_risk_score"].quantile(0.75), color="black", linestyle="--", linewidth=1)
    ax.axhline(df["CLV"].quantile(2 / 3), color="black", linestyle="--", linewidth=1)
    ax.set_xlabel("Churn risk score")
    ax.set_ylabel("CLV ($)")
    ax.set_title("Value Trajectory: CLV x Churn Risk")
    ax.legend(markerscale=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT}/value_trajectory.png", dpi=150)
    plt.close(fig)


def fig_segment_overview():
    df = pd.read_csv("data/processed/segmented_customers.csv")
    profile = df.groupby("segment_name").agg(
        n=("Loyalty Number", "size"), clv_mean=("CLV", "mean"), churn_risk_mean=("churn_risk_score", "mean"),
    ).reset_index()
    fig, ax = plt.subplots(figsize=(7, 5))
    # Cooling/Growing Loyalists sit almost on top of each other - alternate
    # label offsets so they don't overlap.
    # Order matches groupby's alphabetical default:
    # Cooling, Dormant, Growing, New/Onboarding, VIP
    offsets = [(-55, 10), (0, 14), (55, 10), (0, 14), (0, 14)]
    for (_, row), off in zip(profile.iterrows(), offsets):
        ax.scatter(row["churn_risk_mean"], row["clv_mean"], s=row["n"] / 5,
                   alpha=0.7, edgecolors="black", linewidth=0.5)
        ax.annotate(f"{row['segment_name']}\n(n={int(row['n']):,})",
                    (row["churn_risk_mean"], row["clv_mean"]),
                    textcoords="offset points", xytext=off, ha="center", fontsize=8)
    ax.set_xlabel("Avg. predicted churn risk")
    ax.set_ylabel("Avg. CLV ($)")
    ax.set_title("Segments: size, value, and risk")
    fig.tight_layout()
    fig.savefig(f"{OUT}/segment_overview.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_feature_importance()
    fig_value_trajectory()
    fig_segment_overview()
    print("Saved figures to figures/")
