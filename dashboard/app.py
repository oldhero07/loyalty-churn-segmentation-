"""
PS3 - Airline Loyalty: Behavioral Intelligence Dashboard

Audience: marketing manager (non-technical). Goal: surface WHO needs
attention and WHAT to do, backed by the churn model + segmentation +
value-trajectory analysis built in src/.

Run with:  streamlit run dashboard/app.py   (from the project root)
"""
import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Loyalty Retention Dashboard", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join(DATA_DIR, "segmented_customers.csv"))
    return df


df = load_data()

# Active population = "at risk" entering 2018, i.e. exclude pre-2017
# already-departed members from headline metrics (they are not actionable).
active = df[df["in_cohort"] == 1].copy()

st.title("Airline Loyalty - Behavioral Intelligence Dashboard")
st.caption(
    "Built on 2017 behavior to predict 2018 churn risk, segment members "
    "beyond CLV, and recommend a specific retention action per member."
)

tab_overview, tab_action, tab_lookup, tab_about = st.tabs(
    ["Executive Overview", "Action Center", "Member Lookup", "How this works"]
)

# ---------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# ---------------------------------------------------------------------------
with tab_overview:
    st.subheader("Portfolio at a glance")

    total_members = len(active)
    total_clv = active["CLV"].sum()
    avg_churn_risk = active["churn_risk_score"].mean()
    clv_at_risk = (active["CLV"] * active["churn_risk_score"]).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active members", f"{total_members:,}")
    c2.metric("Total CLV", f"${total_clv/1e6:,.1f}M")
    c3.metric("Avg. predicted churn risk", f"{avg_churn_risk:.1%}")
    c4.metric("CLV-weighted risk exposure", f"${clv_at_risk/1e6:,.1f}M",
              help="Sum of (CLV x churn_risk_score) across all active members - "
                   "an estimate of CLV that could be lost if no action is taken.")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Segments: size vs. value vs. risk")
        seg_summary = active.groupby("segment_name").agg(
            members=("Loyalty Number", "size"),
            avg_clv=("CLV", "mean"),
            avg_churn_risk=("churn_risk_score", "mean"),
            actual_churn_rate=("blended_churn", "mean"),
        ).reset_index()
        fig = px.scatter(
            seg_summary, x="avg_churn_risk", y="avg_clv", size="members",
            color="segment_name", text="segment_name",
            labels={"avg_churn_risk": "Avg. predicted churn risk",
                    "avg_clv": "Avg. CLV ($)", "segment_name": "Segment"},
            size_max=60,
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        st.plotly_chart(fig, width='stretch')
        st.caption(
            "Bubble size = number of members. Segments to the right (high "
            "predicted risk) AND high on the chart (high CLV) are the most "
            "valuable to protect."
        )

    with col2:
        st.markdown("#### Value Trajectory: CLV x Churn Risk")
        vq_summary = active.groupby("value_quadrant").agg(
            members=("Loyalty Number", "size"),
            avg_clv=("CLV", "mean"),
            avg_risk=("churn_risk_score", "mean"),
            actual_churn_rate=("blended_churn", "mean"),
        ).reset_index()
        fig2 = px.scatter(
            vq_summary, x="avg_risk", y="avg_clv", size="members",
            color="value_quadrant", text="value_quadrant",
            color_discrete_map={
                "At-Risk High Value": "#d62728",
                "Protected Core": "#2ca02c",
                "Win-Back Priority": "#9467bd",
                "Steady Base": "#7f7f7f",
            },
            labels={"avg_risk": "Avg. predicted churn risk",
                    "avg_clv": "Avg. CLV ($)", "value_quadrant": "Quadrant"},
            size_max=60,
        )
        fig2.update_traces(textposition="top center")
        fig2.update_layout(showlegend=False, yaxis_tickprefix="$")
        st.plotly_chart(fig2, width='stretch')
        st.caption(
            "CLV alone says nothing about risk (correlation ~= 0.01). "
            "'At-Risk High Value' members have CLV almost identical to "
            "'Protected Core' ($14.9k vs $14.4k avg) but a churn risk score "
            "~8x higher (0.26 vs 0.03), matching their actual churn rate "
            "(27% vs 2%) - see reports/supporting_analysis/value_trajectory.md."
        )

    st.divider()
    st.markdown("#### Headline finding")
    arhv = active[active["value_quadrant"] == "At-Risk High Value"]
    pcore = active[active["value_quadrant"] == "Protected Core"]
    st.warning(
        f"**${arhv['CLV'].sum()/1e6:,.1f}M of CLV** ({len(arhv):,} members) "
        f"sits in **'At-Risk High Value'** members the model flags as "
        f"elevated-risk (avg score {arhv['churn_risk_score'].mean():.0%}, "
        f"matching their actual churn rate of "
        f"{arhv['blended_churn'].mean():.0%}). Their average CLV "
        f"(${arhv['CLV'].mean():,.0f}) is statistically indistinguishable "
        f"from the 'Protected Core' (${pcore['CLV'].mean():,.0f} avg, only "
        f"{pcore['blended_churn'].mean():.0%} actual churn) - a CLV-only "
        f"report would never separate these two groups, even though one "
        f"needs a save campaign and the other needs recognition."
    )

# ---------------------------------------------------------------------------
# TAB 2: ACTION CENTER
# ---------------------------------------------------------------------------
with tab_action:
    st.subheader("What to do, by action group")
    st.caption(
        "Each member is assigned ONE action group based on their segment, "
        "value trajectory, and tenure - see reports/supporting_analysis/retention_playbook.md "
        "for the full rationale."
    )

    action_summary = active.groupby(
        ["action_group", "recommended_action", "timing", "success_metric"]
    ).agg(
        members=("Loyalty Number", "size"),
        total_clv=("CLV", "sum"),
        avg_churn_risk=("churn_risk_score", "mean"),
    ).reset_index().sort_values("total_clv", ascending=False)

    action_summary["total_clv"] = action_summary["total_clv"].map(lambda x: f"${x/1e6:,.1f}M")
    action_summary["avg_churn_risk"] = action_summary["avg_churn_risk"].map(lambda x: f"{x:.1%}")

    st.dataframe(
        action_summary.rename(columns={
            "action_group": "Action group", "recommended_action": "Recommended action",
            "timing": "Timing / trigger", "success_metric": "Success metric",
            "members": "Members", "total_clv": "Total CLV", "avg_churn_risk": "Avg. churn risk",
        }),
        width='stretch', hide_index=True,
    )

    st.divider()
    st.markdown("#### Drill into a group: top members to act on first")

    action_groups = sorted(active["action_group"].unique())
    default_idx = action_groups.index("VIP win-back (urgent)") if "VIP win-back (urgent)" in action_groups else 0
    chosen = st.selectbox("Choose an action group", action_groups, index=default_idx)

    subset = active[active["action_group"] == chosen].copy()
    subset["clv_at_risk"] = subset["CLV"] * subset["churn_risk_score"]
    subset = subset.sort_values("clv_at_risk", ascending=False)

    show_cols = [
        "Loyalty Number", "segment_name", "value_quadrant", "CLV",
        "churn_risk_score", "recency_months", "momentum", "tenure_years",
        "recommended_action", "timing", "success_metric",
    ]
    display = subset[show_cols].head(50).rename(columns={
        "Loyalty Number": "Member ID", "segment_name": "Segment",
        "value_quadrant": "Value quadrant", "CLV": "CLV ($)",
        "churn_risk_score": "Churn risk", "recency_months": "Months since last flight",
        "momentum": "Momentum (H2-H1 flights)", "tenure_years": "Tenure (yrs)",
        "recommended_action": "Action", "timing": "Timing", "success_metric": "Success metric",
    })
    display["CLV ($)"] = display["CLV ($)"].map(lambda x: f"${x:,.0f}")
    display["Churn risk"] = display["Churn risk"].map(lambda x: f"{x:.1%}")
    display["Tenure (yrs)"] = display["Tenure (yrs)"].round(1)

    st.write(f"Showing top {len(display)} of {len(subset):,} members in **{chosen}**, "
             f"ranked by CLV x churn-risk (CLV at risk).")
    st.dataframe(display, width='stretch', hide_index=True)

# ---------------------------------------------------------------------------
# TAB 3: MEMBER LOOKUP
# ---------------------------------------------------------------------------
with tab_lookup:
    st.subheader("Look up an individual member")

    member_id = st.number_input(
        "Loyalty Number", min_value=int(df["Loyalty Number"].min()),
        max_value=int(df["Loyalty Number"].max()), value=int(df["Loyalty Number"].iloc[0]), step=1,
    )

    match = df[df["Loyalty Number"] == member_id]
    if match.empty:
        st.error("No member found with that Loyalty Number.")
    else:
        row = match.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Segment", row["segment_name"])
        c2.metric("Value quadrant", row["value_quadrant"])
        c3.metric("CLV", f"${row['CLV']:,.0f}")
        c4.metric("Churn risk score", f"{row['churn_risk_score']:.1%}")

        st.markdown("#### Recommended action")
        st.info(
            f"**{row['action_group']}**\n\n"
            f"**What to do:** {row['recommended_action']}\n\n"
            f"**When:** {row['timing']}\n\n"
            f"**How we'll know it worked:** {row['success_metric']}"
        )

        st.markdown("#### Behavior snapshot (2017)")
        b1, b2, b3, b4, b5 = st.columns(5)
        b1.metric("Total flights", f"{row['total_flights']:.0f}")
        b2.metric("Months active", f"{row['active_months']:.0f} / 12")
        b3.metric("Months since last flight", f"{row['recency_months']:.0f}")
        b4.metric("Momentum (H2-H1)", f"{row['momentum']:.0f}")
        b5.metric("Tenure (yrs)", f"{row['tenure_years']:.1f}")

# ---------------------------------------------------------------------------
# TAB 4: ABOUT / METHODOLOGY
# ---------------------------------------------------------------------------
with tab_about:
    st.subheader("How this dashboard works")
    st.markdown("""
**1. Churn risk score** - a model trained on each member's 2017 flight
activity, recency, momentum and demographics predicts the probability they
will be inactive or cancel in 2018. Trained and validated on 12,305
established members (AUC 0.78 overall, 0.65 for engaged members - see
`reports/supporting_analysis/churn_model_summary.md`).

**2. Segments (5 groups)** - K-means clustering on engagement, recency,
redemption, tenure and momentum produces 5 behavioral segments: VIP
Loyalists, Growing Loyalists, Cooling Loyalists, Dormant/Lapsed, and
New/Onboarding. See `reports/supporting_analysis/segmentation_summary.md`.

**3. Value Trajectory** - CLV alone tells you almost nothing about risk
(correlation ~= 0.01 with the churn risk score). We pair CLV (top-tercile =
"High CLV", >= $7,997) with the churn risk score (top-quartile = "Elevated
Risk", >= 0.141) to get 4 quadrants: "At-Risk High Value" (high CLV,
elevated risk - the highest-priority save target), "Protected Core" (high
CLV, low risk), "Win-Back Priority" (lower CLV, elevated risk), and "Steady
Base" (lower CLV, low risk). See `reports/supporting_analysis/value_trajectory.md`.

**4. Recommended action** - each member is mapped to ONE of 7 action groups,
based first on tenure status (new vs. established members) and then on the
CLV x churn-risk quadrant, with VIP segment membership determining
white-glove vs. automated channel. Full rationale, triggers and success
metrics for every group are in `reports/supporting_analysis/retention_playbook.md`.

**Known limitations** (also in the technical report):
- Members enrolled during 2018 (3,010 members, "New / Onboarding journey")
  have no 2017 history; their churn scores are extrapolations, flagged
  separately and routed to an onboarding journey regardless of score.
- We checked whether *direction of travel* (H2 vs H1 2017 flight momentum)
  predicts 2018 churn, on the hypothesis that "decelerating" members are at
  risk even if their absolute activity still looks healthy. It does not
  (correlation ~= -0.01) - absolute recency, not the within-year trend, is
  what matters. This changes how "Cooling"
  members should be treated (see `reports/supporting_analysis/segmentation_summary.md`).
- The "newly dark" group (active in 2017, then silent in 2018, 77 members in
  the training cohort) shows ~0 correlation with any 2017 engagement
  feature - the model cannot reliably flag this group in advance.
""")
