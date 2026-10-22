# Evaluation Report (dev split)

- **Images Evaluated**: 24 / 24
- **Images Failed**: 0
- **Rules Excluded (Predicted N/A)**: 6

## Overall Summary

| Metric | Value | Definition |
| :--- | ---: | :--- |
| Total Rule Evaluations | 226 | Excludes skipped 'n/a' rules |
| Rules Excluded (Predicted N/A) | 6 | Excluded from metrics (e.g. R02/R03 when net quantity missing) |
| True Positives (TP) | 24 | Expected fail, predicted FAIL |
| False Negatives (FN) | 0 | Expected fail, predicted PASS (missed defect) |
| Caught for Review | 0 | Expected fail, predicted NEEDS_REVIEW |
| False Positives (FP) | 0 | Expected pass, predicted FAIL (false alarm) |
| Review Burden | 0 | Expected pass, predicted NEEDS_REVIEW |
| True Negatives (TN) | 202 | Expected pass, predicted PASS |
| **Precision** | **100.0%** | `TP / (TP + FP)` |
| **Recall** | **100.0%** | `TP / (TP + FN + Caught)` |
| **Recall (with review)** | **100.0%** | `(TP + Caught) / (TP + FN + Caught)` |
| **False Alarm Rate** | **0.0%** | `FP / (FP + TN + Review-burden)` |
| **Review Rate** | **0.0%** | `(Caught + Review-burden) / Total` |

## Per-Rule Breakdown

| Rule | Total | TP | FN | Caught | FP | Burden | TN | Precision | Recall | Recall (w/ Rev) | False Alarm Rate | Review Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R01 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R02 | 21 | 1 | 0 | 0 | 0 | 0 | 20 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R03 | 21 | 1 | 0 | 0 | 0 | 0 | 20 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R04 | 24 | 4 | 0 | 0 | 0 | 0 | 20 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R05 | 20 | 0 | 0 | 0 | 0 | 0 | 20 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| R06 | 20 | 3 | 0 | 0 | 0 | 0 | 17 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R07 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R08 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R09 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R10 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

## Per-Product Breakdown

| Product | Total | TP | FN | Caught | FP | Burden | TN | Precision | Recall | Recall (w/ Rev) | False Alarm Rate | Review Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| biscuit | 48 | 5 | 0 | 0 | 0 | 0 | 43 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| chips | 48 | 5 | 0 | 0 | 0 | 0 | 43 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| juice | 48 | 5 | 0 | 0 | 0 | 0 | 43 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| masala | 50 | 5 | 0 | 0 | 0 | 0 | 45 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| salt | 32 | 4 | 0 | 0 | 0 | 0 | 28 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

## Wrong Predictions (0)

*(None! All predictions matched expected ground truth)*
