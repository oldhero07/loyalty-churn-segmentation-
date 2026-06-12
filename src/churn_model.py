"""
Churn prediction model.

Label: blended_churn (hard_churn OR behavioral_churn in 2018), predicted using
ONLY 2017 (observation-window) features -> no leakage.

We report:
  - Overall model performance (AUC, PR-AUC) on the full cohort.
  - Performance separately for the "was_active_2017" subgroup, since the
    "already dark" segment (was_active_2017 == 0) is trivially separable
    (they were already at 0 engagement) and would inflate apparent
    performance if not called out.
  - Feature importance for interpretation.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report

NUMERIC_FEATURES = [
    "total_flights", "total_distance", "total_points_accumulated",
    "total_points_redeemed", "total_dollar_redeemed", "active_months",
    "pct_months_active", "avg_flights_per_active_month", "flight_volatility",
    "redemption_rate", "has_redeemed", "recency_months", "h1_flights",
    "h2_flights", "momentum", "redemption_momentum", "distance_per_flight",
    "Salary", "salary_missing", "tenure_years",
]
# NOTE: CLV is deliberately excluded. It shows ~0 correlation with every other
# field in the dataset (flight activity, distance, tenure, salary - all |r| <
# 0.04), suggesting it is independently/synthetically assigned rather than
# derived from observable behavior. Including it added no signal (importance
# ~2%) and it is not a clean "observation-window" feature (it's a lifetime
# snapshot). CLV is retained for the value/segmentation analysis only, where
# it is paired with momentum (see value_trajectory.py / reports/supporting_analysis/value_trajectory.md).
CATEGORICAL_FEATURES = ["Gender", "Education", "Marital Status", "Loyalty Card",
                         "Enrollment Type", "Province"]
LABEL = "blended_churn"


def load_data():
    return pd.read_csv("data/processed/model_dataset.csv")


def build_pipeline(model):
    pre = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline([("pre", pre), ("model", model)])


def evaluate(name, y_true, y_proba, subset_mask=None, label_subset=""):
    if subset_mask is not None:
        y_true = y_true[subset_mask]
        y_proba = y_proba[subset_mask]
    if y_true.nunique() < 2:
        print(f"{name} {label_subset}: only one class present, skipping AUC")
        return
    auc = roc_auc_score(y_true, y_proba)
    ap = average_precision_score(y_true, y_proba)
    print(f"{name} {label_subset}: AUC={auc:.3f}  PR-AUC={ap:.3f}  "
          f"(n={len(y_true)}, positive rate={y_true.mean():.3f})")


def main():
    full_df = load_data()
    df = full_df[full_df["in_training_cohort"] == 1].copy()
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[LABEL]

    print(f"Training cohort: {len(df)} members "
          f"(established before {2017+1}, not cancelled by end of 2017)")
    print(f"Excluded from training: "
          f"{full_df['in_cohort'].sum() - len(df)} members enrolled in 2018 "
          f"(no 2017 history) - scored separately below.\n")

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.25, random_state=42, stratify=y
    )

    models = {
        "LogisticRegression": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "GradientBoosting": GradientBoostingClassifier(random_state=42),
    }

    for name, model in models.items():
        pipe = build_pipeline(model)
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]

        print(f"\n=== {name} ===")
        evaluate(name, y_test, proba, label_subset="(overall)")

        was_active = df.loc[idx_test, "was_active_2017"].values
        evaluate(name, y_test, proba, subset_mask=(was_active == 1), label_subset="(was_active_2017=1)")
        evaluate(name, y_test, proba, subset_mask=(was_active == 0), label_subset="(was_active_2017=0, dormant)")

    # Final model: GradientBoosting on full data, for feature importance + scoring
    final_model = build_pipeline(GradientBoostingClassifier(random_state=42))
    final_model.fit(X, y)

    # Feature importance
    ohe = final_model.named_steps["pre"].named_transformers_["cat"]
    cat_names = ohe.get_feature_names_out(CATEGORICAL_FEATURES)
    all_names = NUMERIC_FEATURES + list(cat_names)
    importances = final_model.named_steps["model"].feature_importances_
    imp_df = pd.DataFrame({"feature": all_names, "importance": importances}).sort_values(
        "importance", ascending=False
    )
    print("\n=== Top 15 feature importances (full-data GBM) ===")
    print(imp_df.head(15).to_string(index=False))

    # Score the broader scoring cohort (in_cohort), including 2018 enrollees who
    # were excluded from training. Their scores are extrapolations from
    # established-member patterns and are flagged via `in_training_cohort`.
    score_df = full_df[full_df["in_cohort"] == 1].copy()
    X_score = score_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    score_df["churn_risk_score"] = final_model.predict_proba(X_score)[:, 1]
    score_df[["Loyalty Number", "churn_risk_score", "blended_churn", "hard_churn",
              "behavioral_churn", "was_active_2017", "in_training_cohort"]].to_csv(
        "data/processed/churn_scores.csv", index=False
    )
    print("\nSaved churn_scores.csv")
    imp_df.to_csv("data/processed/feature_importance.csv", index=False)


if __name__ == "__main__":
    main()
