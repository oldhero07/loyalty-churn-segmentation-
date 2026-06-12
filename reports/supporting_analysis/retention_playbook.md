# Smart Retention Playbook

Every member in the 15,315-member "at risk entering 2018" cohort is mapped to
**exactly one of 7 action groups**, by `src/retention_actions.py` (priority
order matters -- the first matching rule wins):

1. Tenure status first -- members enrolled during 2018
   (`in_training_cohort == 0`) get a dedicated onboarding journey regardless
   of their value/risk profile, because their churn drivers (and their
   model scores -- see `churn_model_summary.md`) are different in kind from
   established members.
2. For established members, the **CLV x churn-risk `value_quadrant`** from
   `value_trajectory.py` (At-Risk High Value / Protected Core / Win-Back
   Priority / Steady Base) determines the treatment.
3. **VIP Loyalists** get a white-glove (manual/relationship-desk) version of
   the same treatment where the segment overlaps an elevated-risk or
   high-CLV quadrant; everyone else gets the automated version.

For every group we specify **who** receives the action, **why**, the
**trigger**, the **channel/form and timing**, and the **success metric** --
no group gets a generic "send a discount email." All sizes, CLV and churn
figures below are computed directly from `segmented_customers.csv`.

---

## 1. New / Onboarding journey (HIGHEST VOLUME)
- **Who**: 3,010 members enrolled during 2018 (`in_training_cohort == 0`,
  `tenure_years == 0` by construction). $24.1M total CLV (avg $8,020/member),
  avg model risk score 0.209, **actual churn rate 18.1%** -- by far the
  highest of any action group except the urgent win-back groups.
- **Why**: New members have zero 2017 history, so the churn model's score
  for this group is an **extrapolation**, not a validated prediction (see
  `churn_model_summary.md`). Their churn drivers are onboarding friction and
  unmet first-impression expectations, not the recency/tenure decay that
  drives the model for established members -- this group needs a structured
  first-year journey, not a model-triggered offer.
- **Trigger**: `in_training_cohort == 0` -- applies at enrollment, regardless
  of `value_quadrant`.
- **Form / Channel**: Welcome series (automated email/app) with a
  first-flight bonus-points target, a 30-day check-in nudge if no activity
  yet, and a 90-day "redeem your first reward" prompt.
- **Timing**: Always-on, triggered at enrollment -- the one entry in this
  playbook that runs continuously rather than on a periodic refresh.
- **Success metric**: % of new members completing 1 flight + 1 redemption
  within their first 6 months.
- **Note on internal variation**: this group is *not* uniform -- members who
  also fall in the "At-Risk High Value" or "Win-Back Priority" quadrants
  (960 + 1,942 = 2,902 of 3,010) already show elevated model risk
  (avg 0.21) and a 18-20% churn rate vs. 5.5-5.7% for the small minority
  (108 members) in "Protected Core"/"Steady Base." If onboarding-journey
  capacity is constrained, prioritize the elevated-risk majority first.

## 2. VIP win-back (urgent)
- **Who**: 33 members. **VIP Loyalists** segment, "At-Risk High Value"
  quadrant (CLV >= $7,997 top-tercile AND churn-risk score >= 0.141 top
  quartile). Avg CLV **$35,403** ($1.17M total), avg risk score 0.473,
  **actual churn rate 54.5%** -- the highest of any group.
- **Why**: This is the smallest but highest-stakes group -- the airline's
  most valuable members, already showing the model's strongest risk signal.
  The gap between their CLV ($35,403, near the top of the membership base)
  and the typical "Protected Core" VIP ($27,143 avg, see group 5) is modest,
  but their risk score and actual outcome are night-and-day -- exactly the
  blind spot a CLV-only report would miss (`value_trajectory.md`).
- **Trigger**: `segment_name == "VIP Loyalists" AND value_quadrant ==
  "At-Risk High Value"`.
- **Form / Channel**: Personal outreach -- assigned relationship-desk call
  from a named loyalty manager (not an automated blast), offering a
  **tier-hold guarantee** ("your status is safe for 12 months") plus a
  high-value bonus-mile offer tied to one return flight.
- **Timing**: Within 2 weeks of being flagged (manual queue, reviewed
  weekly) -- a list this small and this valuable warrants white-glove
  timing, not a drip sequence.
- **Success metric**: Reactivation rate within 90 days of contact;
  secondary: CLV retained vs. the $1.17M at risk in this group.

## 3. High-value win-back
- **Who**: 267 members. Non-VIP segments (mostly Dormant/Lapsed, n=178;
  some New/Onboarding-segment and Growing/Cooling members), "At-Risk High
  Value" quadrant. Avg CLV **$12,762** ($3.41M total), avg risk score 0.414,
  actual churn rate **49.1%**.
- **Why**: High CLV (top-tercile) combined with elevated model risk, but
  without the VIP relationship infrastructure -- this group needs a
  scalable, semi-personalized save motion rather than a 1:1 manual queue.
- **Trigger**: `value_quadrant == "At-Risk High Value" AND segment_name !=
  "VIP Loyalists"`.
- **Form / Channel**: Personalized win-back offer (bonus miles tied to the
  member's historical travel pattern -- route, cabin) delivered via
  email/app, plus proactive outreach for the highest-CLV members within the
  group.
- **Timing**: Triggered at the next quarterly segmentation refresh.
- **Success metric**: Reactivation rate within 60 days vs. a held-out
  control group.

## 4. Standard reactivation
- **Who**: 627 members. "Win-Back Priority" quadrant (Low/Mid CLV, elevated
  risk), non-VIP. Avg CLV **$4,815** ($3.02M total), avg risk score 0.412,
  actual churn rate **48.8%** -- nearly identical risk profile to group 3,
  but lower CLV per member.
- **Why**: Same elevated-risk signal as group 3, but the lower per-member
  CLV means the cost-effective treatment is a fully automated sequence
  rather than personalized outreach -- volume-based win-back, not
  relationship-based.
- **Trigger**: `value_quadrant == "Win-Back Priority" AND segment_name !=
  "VIP Loyalists"`.
- **Form / Channel**: 3-email automated win-back series over 6 weeks
  ("we miss you" -> "here's what's new" -> "limited-time bonus miles to fly
  again").
- **Timing**: Triggered on entering this group (next segmentation refresh).
- **Success metric**: Reactivation rate (any flight within 6 months).

## 5. VIP recognition
- **Who**: 783 members. **VIP Loyalists** segment, "Protected Core" quadrant
  (high CLV, lower risk). Avg CLV **$27,143** ($21.25M total), avg risk score
  0.031, actual churn rate **2.6%** -- the airline's healthiest
  high-value relationships.
- **Why**: $21.25M of CLV sits in members the model correctly scores as
  low-risk. The right intervention here is recognition and friction
  reduction to *protect* an already-healthy relationship -- not a "save"
  campaign, which would be wasted spend and could even read as presumptuous
  to a loyal high-value member.
- **Trigger**: `segment_name == "VIP Loyalists" AND value_quadrant ==
  "Protected Core"`.
- **Form / Channel**: Tier-anniversary perks, lounge passes, early access to
  seasonal redemption inventory -- low-cost, high-goodwill, milestone-based.
- **Timing**: Always-on, triggered automatically at enrollment-anniversary
  or flight-count milestones.
- **Success metric**: Year-over-year CLV growth; churn risk score stays low
  at the next refresh.

## 6. Nurture toward VIP
- **Who**: 3,027 members. Non-VIP segments (mostly Cooling Loyalists, n=1,370,
  and Growing Loyalists, n=1,271), "Protected Core" quadrant. Avg CLV
  **$11,134** ($33.7M total), avg risk score 0.034, actual churn rate 2.3%.
- **Why**: This is the largest pool of high-CLV, low-risk members outside
  VIP -- the segment most likely to become tomorrow's VIPs if nurtured, and
  the largest CLV base in the entire cohort ($33.7M) for which "do nothing"
  would be a missed growth opportunity, not just a missed save.
- **Trigger**: `value_quadrant == "Protected Core" AND segment_name !=
  "VIP Loyalists"`.
- **Form / Channel**: Tier-progress nudges ("you're 2 flights from Silver
  status"), targeted partner offers on routes already flown, redemption
  prompts (redemption rates are low across the board).
- **Timing**: Always-on, milestone-triggered.
- **Success metric**: Tier-upgrade rate within 12 months.

## 7. Light-touch monitoring (LARGEST GROUP)
- **Who**: 7,568 members -- the "Steady Base" quadrant (Low/Mid CLV, lower
  risk), non-VIP by construction (no VIP members fall in this quadrant; see
  the quadrant x segment crosstab below). Avg CLV **$4,661** ($35.3M total),
  avg risk score 0.033, actual churn rate 2.8%.
- **Why**: Half the cohort by count, but the lowest CLV-per-member and lowest
  risk of any group -- heavy personal outreach here would not be
  cost-effective. The right motion is cheap, automated, and scalable.
- **Trigger**: `value_quadrant == "Steady Base" AND segment_name != "VIP
  Loyalists"` (catch-all for everyone not matched above).
- **Form / Channel**: Fully automated quarterly "here's what you can redeem"
  email and generic seasonal promos. No human review.
- **Timing**: Scheduled quarterly batch send.
- **Success metric**: Email open/click-through rate and incremental
  bookings vs. a no-contact control -- kept cheap because expected value per
  member is low.

---

## Reference: value_quadrant x segment crosstab (established members only, n=12,305)

|  | Cooling | Dormant | Growing | New/Onboard. | VIP |
|---|---|---|---|---|---|
| At-Risk High Value | 14 | 751 | 53 | 345* | 97 |
| Protected Core | 1,381 | 21 | 1,273 | 381* | 789 |
| Steady Base | 3,436 | 25 | 3,277 | 903* | 0 |
| Win-Back Priority | 62 | 1,568 | 124 | 815* | 0 |

\* The "New/Onboarding" *behavioral segment* (2,444 members, defined by very
low 2017 engagement) is distinct from the "enrolled-in-2018" group routed to
action group 1 (3,010 members, defined by `in_training_cohort`) -- the two
overlap but are not identical. Members in this column who are *also*
enrolled-in-2018 go to action group 1; the rest are distributed to groups
3/4/6/7 by their quadrant as normal.

---

## Cross-cutting principle: tenure status, then value x risk -- never the
## churn score alone
Every group above is defined by **at least two** of (a) tenure status
(new vs. established, group 1), (b) the CLV-tier x churn-risk-tier quadrant
(groups 2-4, 5-7), and (c) VIP segment membership as a tone/channel
tie-breaker (groups 2 vs. 3, 5 vs. 6). This directly reflects the two biggest
limitations of the model found during development
(`churn_model_summary.md`):
1. The score is an **extrapolation** for the 3,010 members enrolled in 2018
   (group 1) -- useful for relative prioritization within that group, not as
   a precise probability.
2. For established members, the score **is** well-calibrated (avg risk
   0.41-0.47 vs. actual churn 0.49-0.55 in the elevated-risk groups; avg risk
   0.03 vs. actual churn 0.02-0.03 in the low-risk groups) -- which is why,
   for this population, it is the primary driver of group assignment, with
   CLV determining *how* (manual vs. automated, save vs. nurture) rather than
   *whether* a member gets attention.
