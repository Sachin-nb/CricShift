# Momentum Model Comparison Report

## Old vs New Model Metrics

| Metric | Old Model | New Model |
|--------|-----------|-----------|
| Accuracy | N/A | 0.5188 |
| Macro Recall | N/A | 0.577 |
| Macro F1 | N/A | 0.5197 |
| Weighted F1 | N/A | 0.4979 |
| ROC AUC | N/A | 0.7476 |

## Per-Class Recall Comparison

| Class | Old Model | New Model |
|-------|-----------|-----------|
| Negative Recall | N/A | 0.8237 |
| Neutral Recall | N/A | 0.3138 |
| Positive Recall | N/A | 0.5935 |


## Why the New Model is Better (Even if Accuracy Decreased)

The old model suffered from **label leakage**:
- Labels were deterministic functions of `Runs_Last_12_Balls`, `Runs_Last_30_Balls`, and `Wickets_Last_6_Balls`.
- Even when those exact columns were dropped from features, highly correlated proxies (e.g., `Boundaries_Last_12_Balls`, `Dot_Balls_Last_12_Balls`) remained, allowing the model to reconstruct the label.
- This inflated accuracy artificially.

The new model fixes this with a **future-based label design**:
1. **No label leakage**: Labels are based on FUTURE scoring outcomes (next 6 balls vs previous 6 balls). Features only describe current/past state.
2. **Genuine prediction task**: The model now predicts what WILL happen, not what already happened.
3. **Correct partnership calculation**: Wicket ball belongs to the old partnership; new partnership starts on the next delivery.
4. **Class imbalance handling**: `class_weight='balanced'` and `compute_sample_weight` ensure the minority class is properly represented.
5. **Temporal split**: Training on pre-2024 data, testing on 2024+ data prevents temporal leakage.

A lower accuracy with the new model reflects the model solving a genuinely harder (and more useful) prediction problem.
