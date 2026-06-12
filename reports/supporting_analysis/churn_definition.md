# Churn Definition

## Setup: avoiding leakage
- **Observation window = 2017** (Jan-Dec): all predictive features are built from
  this window only.
- **Outcome window = 2018** (Jan-Dec): churn labels are evaluated here.
- **Modeling cohort** = 15,315 members who were *not yet cancelled* as of
  2017-12-31 (i.e., "at risk" entering 2018). 1,422 members who had already
  cancelled before/during 2017 are excluded — they are already churned and
  contain no forward-looking signal.

## Two competing definitions tested

### A. Hard churn — formal cancellation
`Cancellation Year == 2018` → **4.21%** of cohort (645 members).

- Pro: unambiguous, directly actionable (member explicitly left).
- Con: **lagging and weakly related to prior engagement**. Correlation between
  2017 engagement (`pct_months_active`) and hard churn is only **-0.10**, and
  with `recency_months` it is **~0.00**. Many members who cancel in 2018 were
  flying normally in 2017 — cancellation appears driven by factors *outside*
  this dataset (price, life events, switching programs), not visible
  disengagement.

### B. Behavioral (soft) churn — zero flight activity in 2018
`total_flights_2018 == 0` → **4.58%** of cohort (701 members).

- Pro: catches "ghost members" the cancellation flag misses entirely — **661
  of 701** behavioral churners never formally cancelled.
- Con: of these 701, **624 (89%) were *already* fully inactive in 2017 too**
  (`pct_months_active == 0`). For this majority, "churn in 2018" isn't a new
  event we can predict — it's the *continuation* of a pre-existing dormant
  state that started before our observation window even begins.

### Overlap
Only **40 members** satisfy both A and B — formal cancellation and complete
behavioral dropout are **largely different populations**.

## Decomposition: the population actually splits into three groups

| Segment | Size | Hard churn rate | 2017 engagement | Interpretation |
|---|---|---|---|---|
| **Newly dark** (active in 2017, zero flights 2018) | 77 | 45.5% | normal (avg) | Genuine, recent departures — but **not predictable from 2017 engagement levels alone** (corr ≈ 0 with all engagement features). Likely driven by external triggers. |
| **Already dark** (zero flights in both 2017 and 2018, never cancelled) | 624 | 0.8% | none | A **structurally dormant segment present from day one** — not "churning," they were never really engaged. Different problem: reactivation, not retention. |
| **Hard-churn-only** (cancelled 2018, kept flying in 2018 on the dataset) | 605 | — | above-average (29% months active) | Engaged members who formally exit — the cancellation event itself carries the signal, not flight activity. |

## Decision: Blended definition, used with segment context

**Primary churn label = `hard_churn OR behavioral_churn`** ("blended churn",
8.53% of cohort), because:
1. It is the only definition that captures *both* the explicit-exit and
   silent-attrition failure modes the airline cares about (per the brief:
   "some customers stop flying... others remain enrolled but stop earning or
   redeeming points").
2. It has materially higher correlation with 2017 engagement signals
   (`recency_months` r = 0.30, `pct_months_active` r = -0.30) than hard churn
   alone — i.e., it is more learnable from available data.

**However**, for the retention playbook (not the churn label itself), the
**"already dark" segment (624 members) is treated separately as a reactivation
cohort, not a churn-prevention cohort** — applying retention offers to members
who were never engaged is the wrong intervention. This distinction is encoded
as a feature (`was_active_2017`) and used directly in segmentation
(Task 5) and the retention playbook (Task 6).

## Note: training cohort vs. scoring cohort
The 15,315-member cohort above is the **scoring cohort** (everyone "at risk"
entering 2018). For **model training**, this is further restricted to 12,305
members enrolled on/before 2017 — the 3,010 members enrolled during 2018 have
no 2017 history and are handled separately (see `churn_model_summary.md`).
This does not change the churn definition itself, only which members are used
to fit the model.

## A gap worth flagging (carried into the technical report)
The "newly dark, engaged-then-gone" group — arguably the highest-value
churn-prevention target — is the smallest (77 members) and shows **no
detectable signal in 2017 flight-activity features**. This is a real finding,
not a modeling failure: it suggests that engagement-only data has a structural
blind spot for sudden departures, and the airline would benefit from
additional signals (e.g., customer service contacts, competitor promo
exposure, NPS) to catch this group earlier.
