# PS3 — Unlocking Behavioral Intelligence in Airline Loyalty Programs

**Live dashboard:** https://tduhvbg6cdbabhnt4fjane.streamlit.app/

This project takes the airline loyalty dataset (16,737 members, enrolled between
2012 and 2018, with monthly flight activity for 2017-2018) and turns it into
three things: a churn risk score, a set of behavioral segments that go beyond
CLV, and a retention playbook that tells the marketing team exactly who to
contact and how. The two deliverables are a Streamlit dashboard
(`dashboard/app.py`) and a written technical report
(`reports/technical_report.md`).

## Project structure

```
PS3_Airline_Loyalty/
├── data/
│   ├── raw/              # the four original CSVs, untouched
│   └── processed/        # cleaned + feature-engineered outputs
├── notebooks/            # exploration, feature engineering, modeling, segmentation
├── src/                  # the actual pipeline, runnable end to end
├── dashboard/            # the Streamlit prototype
├── reports/              # technical report + supporting write-ups
├── figures/              # charts used in the report and dashboard
└── requirements.txt
```

## How the analysis is put together

### Defining churn (there's no churn column in the raw data)

The dataset has an enrollment/cancellation date and a monthly flight log, but
nothing that says "this member churned." So the first real decision was how to
define it. Two candidates were tested on the 15,315 members who were still
enrolled going into 2018: a **hard** definition (formally cancelled during
2018 — 4.2% of members) and a **behavioral** one (zero flights at all in
2018 — 4.6%). Only 40 members satisfy both, which tells you these are mostly
different populations — someone can stop flying long before they bother to
cancel, and vice versa. Using either definition alone would miss the other
group entirely, so the final label is the union of the two:
`blended_churn = hard_churn OR behavioral_churn`, landing at 8.5% of the
cohort. The full reasoning is in `reports/supporting_analysis/churn_definition.md`.

Everything downstream respects a strict 2017-vs-2018 split: every feature used
for modeling or segmentation comes from 2017 behavior, and 2018 is only used to
check whether someone churned. Nothing from the outcome period leaks into the
inputs.

### The churn model

A GradientBoostingClassifier trained on 2017 behavior (flight volume, recency,
momentum, redemption activity) plus demographics (salary, education, marital
status, card tier, province, enrollment type) and tenure. It scores 0.775 AUC
overall, but that number is inflated by members who had already gone dark
*before* 2017 — for the population you'd actually target with a retention
campaign (people who were still flying in 2017), AUC drops to a more honest
0.654. `recency_months` and `tenure_years` alone account for ~83% of the
model's decisions, which is reassuring in a "this isn't a black box" sense:
the model is mostly just learning "how long since they last flew" and "how
long have they been a member," which is exactly what you'd expect a human
analyst to look at first.

One subtlety: the 3,010 members who enrolled *during* 2018 have no 2017
history at all, so their feature vectors are all zeros — identical, on paper,
to a long-tenured member who's gone completely dormant. Training on both
groups together would teach the model a lazy "no history = high risk" shortcut
that conflates two very different situations. So the model is trained only on
the 12,305 members enrolled by 2017, and the 2018 cohort is scored afterward
as an extrapolation and routed to its own onboarding track instead of a
churn-risk-based one. Details in `reports/supporting_analysis/churn_model_summary.md`.

### Segmentation — and why CLV alone isn't enough

K-means on engagement, recency, redemption, tenure, and momentum produces five
behavioral segments across the 15,315-member cohort: VIP Loyalists (5.8%),
Growing Loyalists (30.9%), Cooling Loyalists (31.9%), New/Onboarding (16.0%),
and Dormant/Lapsed (15.4%). These hold up well — Growing and Cooling Loyalists
look almost identical on raw engagement, but split apart almost entirely on
whether their flight activity is trending up or down within 2017.

The more interesting result came from checking what CLV actually tells you.
The original plan was to pair CLV with that within-year momentum trend (the
idea being that a "decelerating" high-value member is the one worth saving).
That hypothesis didn't survive contact with the data — momentum has
essentially zero correlation with 2018 churn (r ≈ -0.013). What *does*
correlate is plain recency (r ≈ 0.30), which the model already uses. So
instead, CLV gets paired with the churn risk score itself, and that pairing
is where the real finding is: CLV and churn risk are almost completely
uncorrelated (r ≈ 0.01). Concretely, $18.8M of CLV sits in 1,260 members the
model flags as elevated risk (avg score 26%, matching their actual 27% churn
rate) — and their average CLV is statistically indistinguishable from the
"Protected Core" group that's churning at 2%. A report built on CLV alone
would never separate these two groups, even though one needs a retention
campaign and the other needs a thank-you. This is written up in
`reports/supporting_analysis/value_trajectory.md`, with the segment detail in
`reports/supporting_analysis/segmentation_summary.md`.

### The retention playbook

Every member lands in exactly one of seven action groups, decided in this
order: tenure status first (the 2018 enrollees get an onboarding journey
regardless of anything else, since their model score is an extrapolation),
then the CLV × churn-risk quadrant (At-Risk High Value, Protected Core,
Win-Back Priority, Steady Base), and finally VIP segment membership as a
tone/channel decision (white-glove outreach vs. an automated email). The
seven groups range from a 33-person "VIP win-back, urgent" list with a 54.5%
actual churn rate that goes to a relationship manager within two weeks, down
to a 7,568-member "light-touch monitoring" group that just gets a quarterly
automated email. Each group's trigger, channel, timing, and success metric is
in `reports/supporting_analysis/retention_playbook.md`.

## The deliverables

**Dashboard** (`dashboard/app.py`) — four tabs: an executive overview with the
portfolio-level numbers and the CLV-vs-risk chart, an action center where you
can drill into any of the seven groups and see the highest-priority members
first, a member lookup for individual accounts, and a "how this works" tab
that explains the methodology in plain language.

**Technical report** (`reports/technical_report.md`, ~6.3 pages) — problem
framing, the cleaning and churn-definition decisions, how the model and
segmentation work, the key findings above, and three recommendations sized
for a CFO/CMO conversation.

## Running it

```powershell
cd PS3_Airline_Loyalty
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Rebuilding the pipeline from scratch

`data/processed/` already has everything generated, but if you want to
reproduce it, run these in order from the project root:

```powershell
python src/data_prep.py        # clean raw data -> *_clean.csv
python src/features.py          # feature engineering -> model_dataset.csv
python src/churn_model.py       # train model -> churn_scores.csv, feature_importance.csv
python src/segmentation.py      # K-means segments -> segmented_customers.csv
python src/value_trajectory.py  # CLV x churn-risk quadrants
python src/retention_actions.py # assign action groups
python src/make_figures.py      # regenerate figures/*.png
```

## Where this falls short

- The 3,010 members enrolled in 2018 have no 2017 history, so their churn
  scores are extrapolations rather than validated predictions — that's why
  they get their own onboarding track instead of a score-based one.
- The momentum-based hypothesis didn't pan out (see above) — it's reported
  here rather than quietly dropped, because it changes how "Cooling Loyalists"
  should actually be treated.
- There's a small group (77 members, in the training cohort) who were active
  in 2017 and went completely silent in 2018 with no warning signs in their
  2017 data. The model can't catch this group in advance, and no amount of
  tuning fixes that — it's a data gap, not a modeling one.
