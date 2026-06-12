# Customer Segmentation & Value

KMeans (k=5, silhouette ~= 0.30) on standardized behavioral + value features:
`CLV`, `total_flights`, `pct_months_active`, `recency_months`,
`redemption_rate`, `tenure_years`, `momentum` (H2-H1 2017 flight activity).

Segmentation runs on the **15,315-member "at risk entering 2018" cohort**
(`in_cohort == 1`) -- the same population used for churn modeling. The 1,422
members already cancelled on/before 2017 are excluded: they are guaranteed
`blended_churn == 1` by construction (already gone before the observation
window even ends), and including them would distort every segment's "actual
churn rate" by however many of these already-departed members it happened to
contain.

## Why not just CLV?
CLV barely varies across 4 of the 5 segments (~$6,400-$7,600) and is
essentially independent of every behavioral and risk signal (see
`churn_model_summary.md` and `value_trajectory.md`: corr(CLV, churn_risk) ~=
0.01, corr(CLV, blended_churn) ~= 0.001) -- **CLV measures historical revenue,
not current engagement or risk**. The segmentation adds the "who is this
customer today, and how engaged are they" dimension that CLV misses entirely.

## The five segments

| Segment | Size | % | Avg CLV | Engagement (2017) | Momentum (H2-H1) | Churn risk score | Actual churn rate |
|---|---|---|---|---|---|---|---|
| **VIP Loyalists** | 886 | 5.8% | $28,287 | 53% months active, recency 1.1 | +1.7 | 0.06 | 5.0% |
| **Growing Loyalists** | 4,727 | 30.9% | $6,416 | 62% months active, recency 0.4 | **+6.2** | 0.04 | 3.2% |
| **Cooling Loyalists** | 4,893 | 31.9% | $6,524 | 59% months active, recency 0.9 | **-3.7** | 0.03 | 2.6% |
| **New / Onboarding** | 2,444 | 16.0% | $6,835 | 14% months active, tenure **0.4 yrs** | +3.0 | 0.16 | 12.9% |
| **Dormant / Lapsed** | 2,365 | 15.4% | $7,588 | 0% months active, recency **12.0** | 0.0 | 0.27 | **28.4%** |

### 1. VIP Loyalists (5.8%, n=886)
~4.4x the CLV of any other segment, high and consistent engagement, the
**lowest actual churn rate of any segment (5.0%)**. The airline's most
valuable members -- disproportionate revenue concentration in a small group.

### 2. Growing Loyalists (30.9%, n=4,727)
The healthiest large segment: high engagement, strongly *accelerating*
(momentum +6.2 -- H2 2017 activity roughly 6 flights above H1), low churn
(3.2%).

### 3. Cooling Loyalists (31.9%, n=4,893)
Statistically similar to Growing Loyalists on *current* engagement (59% vs.
62% months active, similar CLV) but trending the **opposite direction**
(momentum -3.7). Despite the negative trend, this segment's **actual churn
rate (2.6%) is the lowest of all five** -- see the finding in
`value_trajectory.md`: within the corrected "at risk" population, H2-H1
momentum on its own is **not** predictive of next-year churn (r ~= -0.01).
Absolute engagement level (`recency_months`, `h1_flights`/`h2_flights`)
drives risk, not the direction of the within-year trend.

### 4. New / Onboarding (16.0%, n=2,444)
Average tenure 0.4 years -- recently enrolled or very low engagement, still
building flying habits (only 14% of months active). **Highest churn rate
among non-dormant segments (12.9%)** -- consistent with new members who
haven't yet formed a habit being most likely to drift away early. (Note:
this behavioral cluster is related to, but not identical to, the
`in_training_cohort == 0` "enrolled in 2018" group used for model scoring --
see `churn_model_summary.md`.)

### 5. Dormant / Lapsed (15.4%, n=2,365)
The segment behind most "behavioral churn": recency 12.0 months (essentially
inactive all year), 99.2% were *already* inactive in 2017
(`was_active_2017` ~= 0.008), and **28.4% are blended-churners** by our
definition -- by far the highest of any segment. As discussed in
`churn_definition.md`, most of this group did not "become" churned during the
observation period -- they were already dormant. **This is a
reactivation/win-back target, not a retention target** (see
`retention_playbook.md`).

## Demographic note
Loyalty Card tier (Star/Nova/Aurora, ~45/34/20% in every non-VIP segment) and
Education distributions are **nearly identical across all 5 segments** --
value and risk are driven by *behavior*, not by which card tier or education
level a member holds. This is an actionable finding: targeting by card tier
alone (a common simplistic approach) would not isolate any of these segments.
