# Churn Model — Methodology & Performance

## Two refinements made during review

1. **CLV excluded from churn-model features.** CLV correlates with
   essentially nothing else in the dataset — flight activity (r ≈ 0.001),
   distance, tenure (r ≈ 0.00), salary (r = -0.02), even cancellation year
   (r = -0.04). This independence suggests CLV is assigned independently of
   observed behavior rather than derived from it. It added negligible model
   signal (~2% importance) and isn't a clean "observation-window" feature
   (it's a lifetime-to-date snapshot that could partially span the outcome
   period). It remains in the **value/segmentation** analysis only, where it
   is explicitly paired with `momentum` (see `value_trajectory.md`) — the
   pairing is itself the point: CLV alone is insufficient.

2. **Training cohort restricted to members enrolled on/before 2017**
   (12,305 of 15,315 scoring-eligible members). The 3,010 members who
   enrolled *during* 2018 have, by construction, zero 2017 history
   (`tenure_years = 0`, all activity features = 0) — identical feature
   vectors to long-tenured-but-dormant members. Including them would let the
   model learn a trivial "no-history -> high churn" rule that conflates
   *new-member* churn (18.1% blended-churn rate) with *established-member*
   churn (6.2%). They are excluded from training/evaluation, then **scored**
   by the fitted model as an extrapolation (flagged via
   `in_training_cohort = 0` in `churn_scores.csv`) and handled operationally
   as the "New / Onboarding" segment.

## Final setup
- **Label**: `blended_churn` = formal cancellation in 2018 OR zero flight
  activity throughout 2018 (see `churn_definition.md`).
- **Features**: 2017-only behavioral features (flight volume, recency,
  momentum, redemption behaviour, distance/flight) + demographics (Salary,
  Education, Marital Status, Loyalty Card, Province, Enrollment Type) +
  tenure. No 2018 information used.
- **Model**: GradientBoostingClassifier (sklearn defaults, random_state=42),
  benchmarked against class-weighted Logistic Regression.

## Performance (held-out 25% test split, training cohort n=12,305)

| Slice | n | Positive rate | AUC | PR-AUC |
|---|---|---|---|---|
| Overall | 3,077 | 6.2% | **0.775** | 0.473 |
| Was active in 2017 (the real retention-targetable population) | 2,938 | 4.0% | **0.654** | 0.109 |
| Was fully dormant in 2017 (training-cohort only, n=139, small sample) | 139 | 51.8% | 0.927* | 0.949* |

\* Small-sample (n=139); directionally consistent (this group is largely
"already dark, stays dark") but not over-interpreted.

## How to read these numbers
- An AUC of 0.654 for the engaged population is **modest but real** — and
  consistent with the `churn_definition.md` finding that the highest-value
  churn-prevention target ("newly dark" members, active in 2017 then silent
  in 2018) shows ~0 correlation with any 2017 engagement feature. A much
  higher AUC here would be a red flag for leakage, not a better model.
- **Top features**: `recency_months` (43%) and `tenure_years` (40%) jointly
  account for ~83% of importance — i.e., "how long since they last flew" and
  "how established they are" are the two dominant, intuitive, and
  non-leaking signals. `distance_per_flight`, `total_distance`, `Salary`,
  and `momentum` contribute the remainder.

## How the score is used
`churn_risk_score` (0-1) is saved per member to `churn_scores.csv` and joined
into the segmentation/dashboard. As shown in `value_trajectory.md`, this
score should be read **alongside CLV**, not in isolation — CLV is
essentially independent of the score (r ≈ 0.01), so a CLV-only view and a
risk-only view surface two different (and roughly equally large) sets of
members. For established members, the score is reasonably well-calibrated
(e.g., the "elevated risk" quadrant averages a 0.41–0.47 predicted score
against a 0.49–0.55 actual churn rate; the "lower risk" quadrants average
0.03 predicted vs. 0.02–0.03 actual) — pairing it with CLV is what turns a
calibrated score into a prioritized worklist (`retention_playbook.md`).
