# Evaluation Report (test split)

- **Images Evaluated**: 34 / 34
- **Images Failed**: 0
- **Rules Excluded (Predicted N/A)**: 4

## Overall Summary

| Metric | Value | Definition |
| :--- | ---: | :--- |
| Total Rule Evaluations | 324 | Excludes skipped 'n/a' rules |
| Rules Excluded (Predicted N/A) | 4 | Excluded from metrics (e.g. R02/R03 when net quantity missing) |
| True Positives (TP) | 24 | Expected fail, predicted FAIL |
| False Negatives (FN) | 0 | Expected fail, predicted PASS (missed defect) |
| Caught for Review | 0 | Expected fail, predicted NEEDS_REVIEW |
| False Positives (FP) | 0 | Expected pass, predicted FAIL (false alarm) |
| Review Burden | 0 | Expected pass, predicted NEEDS_REVIEW |
| True Negatives (TN) | 300 | Expected pass, predicted PASS |
| **Precision** | **100.0%** | `TP / (TP + FP)` |
| **Recall** | **100.0%** | `TP / (TP + FN + Caught)` |
| **Recall (with review)** | **100.0%** | `(TP + Caught) / (TP + FN + Caught)` |
| **False Alarm Rate** | **0.0%** | `FP / (FP + TN + Review-burden)` |
| **Review Rate** | **0.0%** | `(Caught + Review-burden) / Total` |

## Per-Rule Breakdown

| Rule | Total | TP | FN | Caught | FP | Burden | TN | Precision | Recall | Recall (w/ Rev) | False Alarm Rate | Review Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R01 | 34 | 2 | 0 | 0 | 0 | 0 | 32 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R02 | 32 | 4 | 0 | 0 | 0 | 0 | 28 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R03 | 32 | 4 | 0 | 0 | 0 | 0 | 28 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R04 | 34 | 1 | 0 | 0 | 0 | 0 | 33 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R05 | 28 | 4 | 0 | 0 | 0 | 0 | 24 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R06 | 28 | 1 | 0 | 0 | 0 | 0 | 27 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R07 | 34 | 2 | 0 | 0 | 0 | 0 | 32 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R08 | 34 | 2 | 0 | 0 | 0 | 0 | 32 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R09 | 34 | 2 | 0 | 0 | 0 | 0 | 32 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R10 | 34 | 2 | 0 | 0 | 0 | 0 | 32 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

## Per-Product Breakdown

| Product | Total | TP | FN | Caught | FP | Burden | TN | Precision | Recall | Recall (w/ Rev) | False Alarm Rate | Review Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| biscuit | 70 | 5 | 0 | 0 | 0 | 0 | 65 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| chips | 70 | 5 | 0 | 0 | 0 | 0 | 65 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| juice | 70 | 5 | 0 | 0 | 0 | 0 | 65 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| masala | 68 | 5 | 0 | 0 | 0 | 0 | 63 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| salt | 46 | 4 | 0 | 0 | 0 | 0 | 42 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

## Wrong Predictions (0)

*(None! All predictions matched expected ground truth)*
