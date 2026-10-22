# Evaluation Report (dev split)

- **Images Evaluated**: 24 / 24
- **Images Failed**: 0

## Overall Summary

| Metric | Value | Definition |
| :--- | ---: | :--- |
| Total Rule Evaluations | 232 | Excludes skipped 'n/a' rules |
| True Positives (TP) | 21 | Expected fail, predicted FAIL |
| False Negatives (FN) | 2 | Expected fail, predicted PASS (missed defect) |
| Caught for Review | 1 | Expected fail, predicted NEEDS_REVIEW |
| False Positives (FP) | 6 | Expected pass, predicted FAIL (false alarm) |
| Review Burden | 0 | Expected pass, predicted NEEDS_REVIEW |
| True Negatives (TN) | 202 | Expected pass, predicted PASS |
| **Precision** | **77.8%** | `TP / (TP + FP)` |
| **Recall** | **87.5%** | `TP / (TP + FN + Caught)` |
| **Recall (with review)** | **91.7%** | `(TP + Caught) / (TP + FN + Caught)` |
| **False Alarm Rate** | **2.9%** | `FP / (FP + TN + Review-burden)` |
| **Review Rate** | **0.4%** | `(Caught + Review-burden) / Total` |

## Per-Rule Breakdown

| Rule | Total | TP | FN | Caught | FP | Burden | TN | Precision | Recall | Recall (w/ Rev) | False Alarm Rate | Review Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R01 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R02 | 24 | 1 | 0 | 0 | 3 | 0 | 20 | 25.0% | 100.0% | 100.0% | 13.0% | 0.0% |
| R03 | 24 | 1 | 0 | 0 | 3 | 0 | 20 | 25.0% | 100.0% | 100.0% | 13.0% | 0.0% |
| R04 | 24 | 4 | 0 | 0 | 0 | 0 | 20 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R05 | 20 | 0 | 0 | 0 | 0 | 0 | 20 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| R06 | 20 | 3 | 0 | 0 | 0 | 0 | 17 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R07 | 24 | 0 | 2 | 1 | 0 | 0 | 21 | 0.0% | 0.0% | 33.3% | 0.0% | 4.2% |
| R08 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R09 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| R10 | 24 | 3 | 0 | 0 | 0 | 0 | 21 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

## Per-Product Breakdown

| Product | Total | TP | FN | Caught | FP | Burden | TN | Precision | Recall | Recall (w/ Rev) | False Alarm Rate | Review Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| biscuit | 50 | 4 | 1 | 0 | 2 | 0 | 43 | 66.7% | 80.0% | 80.0% | 4.4% | 0.0% |
| chips | 50 | 5 | 0 | 0 | 2 | 0 | 43 | 71.4% | 100.0% | 100.0% | 4.4% | 0.0% |
| juice | 50 | 4 | 1 | 0 | 2 | 0 | 43 | 66.7% | 80.0% | 80.0% | 4.4% | 0.0% |
| masala | 50 | 4 | 0 | 1 | 0 | 0 | 45 | 100.0% | 80.0% | 100.0% | 0.0% | 2.0% |
| salt | 32 | 4 | 0 | 0 | 0 | 0 | 28 | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

## Wrong Predictions (9)

| Image | Rule | Expected | Predicted | Found Value |
| :--- | :--- | :--- | :--- | :--- |
| biscuit_errR01.png | R02 | pass | FAIL | *(empty)* |
| biscuit_errR01.png | R03 | pass | FAIL | *(empty)* |
| biscuit_errR07.png | R07 | fail | PASS | Wheat flour, sugar, palm oil, invert syrup, salt, raising agents |
| chips_errR01.png | R02 | pass | FAIL | *(empty)* |
| chips_errR01.png | R03 | pass | FAIL | *(empty)* |
| juice_errR01.png | R02 | pass | FAIL | *(empty)* |
| juice_errR01.png | R03 | pass | FAIL | *(empty)* |
| juice_errR07.png | R07 | fail | PASS | Water, orange juice concentrate (10%), acidity regulator (330), preservative (223) |
| masala_errR07.png | R07 | fail | NEEDS_REVIEW | Coriander, cumin, black pepper, cinnamon, cloves, bay leaf, salt |
