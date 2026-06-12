# Data Quality Notes & Cleaning Decisions

## Dataset Shapes
- **Customer Loyalty History**: 16,737 customers, 16 columns. No duplicate Loyalty Numbers.
- **Customer Flight Activity**: 392,936 rows, 8 columns, covering **Jan 2017 - Dec 2018 only**
  (24 months) — NOT 2012-2018. The 2012-2018 range applies to *enrollment/cancellation*
  history, not flight activity.
- **Calendar**: daily dimension 2012-01-01 to 2018-12-31 (broader than flight activity needs).

## Key Anomalies & Cleaning Decisions

### 1. Duplicate flight-activity rows
- 3,847 (Loyalty Number, Year, Month) groups have >1 row (7,718 rows total, ~2% of data).
- Of these, **1,914 groups are exact full-row duplicates** (every column identical) →
  **drop via `drop_duplicates()`**.
- The remaining **1,933 groups have differing values** for the same customer/month
  (e.g., two flight segments with different distances) → **aggregate by SUM** at
  (Loyalty Number, Year, Month) grain. This is interpreted as multiple bookings/legs
  recorded separately within the same month.
- Net effect: 392,936 → 389,089 rows, 16,737 customers x up to 24 months.

### 2. Negative salaries (20 records)
- All 20 negative salaries belong to Bachelor's-degree holders with magnitudes
  (-9,081 to -58,486) consistent with the normal salary range (~$30k-$100k).
- **Decision**: treat as a sign-entry error → take `abs(Salary)`.

### 3. Missing salary (4,238 / 16,737 = 25.3%) — NOT random
- **100% of "College"-education customers have missing salary; 0% of any other
  education level is missing.** This is Missing-Not-At-Random (MNAR) — an entire
  segment was never asked/recorded for income, likely because "College" enrollees
  are a different acquisition channel (e.g., 2018 Promotion sign-ups) or
  self-reported income wasn't required for that tier.
- **Decision**: Do NOT impute with a population median (would fabricate signal for
  a quarter of the base). Instead:
  - Add a `salary_missing` flag (≈ redundant with `Education == College` but kept
    explicit for modeling).
  - For modeling, impute missing salary with 0 / median-by-segment only where the
    model requires a numeric value, and rely on Education as the real income proxy
    for this group.

### 4. Cancellation flag is a lagging / unreliable churn signal
- 2,067 / 16,737 (12.3%) customers have a Cancellation Year/Month (spans 2013-2018).
- Spot check: customers who "cancelled" in early 2017 already show **zero flight
  activity for the entire 2017-2018 window** — i.e., disengagement preceded the
  formal cancellation record by months/years.
- Conversely, **605 / 2,067 (29%) of formally "cancelled" members still show flight
  activity in 2018** (after or unrelated to their cancellation date).
- **Implication**: formal cancellation alone underestimates and lags real
  disengagement → motivates a **behavioral churn definition** in addition to the
  formal one (see `churn_definition.md`).

### 5. "Ghost members" — active accounts, zero usage
- 661 / 14,670 (4.5%) of members with **no cancellation record** had **zero flight
  activity across all of 2018**. These are prime behavioral-churn candidates that
  the cancellation flag completely misses.

### 6. Minor: 11-month customers
- 1,623 customers (those enrolled Feb/Mar/Apr 2018) have only 11 monthly rows
  instead of 24, missing Jan 2017-Jan 2018 (pre-enrollment, expected) but Feb 2018
  is present even for March/April enrollees (~1 month early). Immaterial to feature
  windows (all pre-enrollment months are zero-activity by construction); not
  corrected.

### 7. Points Redeemed > Points Accumulated in a given month (3,075 rows)
- Expected and valid: redemption draws from a **cumulative** points balance, not
  the current month's accrual alone. No correction needed.

### 8. CLV vs Salary correlation ≈ -0.02
- CLV is effectively independent of income — CLV appears driven by flight
  behavior/tenure, not affluence. Worth surfacing in segmentation (income ≠ value).
