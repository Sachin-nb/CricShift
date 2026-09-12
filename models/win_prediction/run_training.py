import pandas as pd
import numpy as np
import logging
import json
import time
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split

from utils import create_win_target, select_input_features, preprocess_data, remove_correlated_features
from train_model import train_best_model
from evaluate import evaluate_model, try_calibration
from predict import predict_win_probability

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def main():
    start_time = time.time()

    DATA_PATH = Path(r"data\features\feature_dataset.csv")
    OUTPUT_DIR = Path(r"models\win_prediction")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load Data ──────────────────────────────────────────────
    logging.info("Loading feature dataset...")
    df = pd.read_csv(DATA_PATH, low_memory=False)
    logging.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    # ── Create Target ──────────────────────────────────────────
    logging.info("Creating win target...")
    df = create_win_target(df)
    y = df['Win_Target']

    # ── Select Features ────────────────────────────────────────
    input_features = select_input_features(df)
    X = df[input_features].copy()

    # ── Preprocess ─────────────────────────────────────────────
    logging.info("Preprocessing data...")
    X, encoders = preprocess_data(X)

    # ── Remove Correlated Features ─────────────────────────────
    logging.info("Removing highly correlated features...")
    X, dropped_cols = remove_correlated_features(X)
    feature_columns = X.columns.tolist()
    logging.info(f"Final features: {len(feature_columns)}, dropped {len(dropped_cols)} correlated")

    # ── Temporal Split ─────────────────────────────────────────
    logging.info("Splitting dataset temporally...")
    season_year = df['Season'].astype(str).str[:4].astype(int)

    train_mask = season_year < 2023
    val_mask = season_year == 2023
    test_mask = season_year >= 2024

    X_train_full, y_train_full = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    logging.info(f"Train (< 2023): {len(X_train_full)}")
    logging.info(f"Validation (2023): {len(X_val)}")
    logging.info(f"Test (>= 2024): {len(X_test)}")
    logging.info(f"Train target dist: {dict(y_train_full.value_counts().sort_index())}")
    logging.info(f"Test target dist:  {dict(y_test.value_counts().sort_index())}")

    # ── Downsample for Speed ───────────────────────────────────
    MAX_TRAIN = 10000
    if len(X_train_full) > MAX_TRAIN:
        logging.info(f"Downsampling training set from {len(X_train_full)} to {MAX_TRAIN}...")
        X_train, _, y_train, _ = train_test_split(
            X_train_full, y_train_full,
            train_size=MAX_TRAIN, stratify=y_train_full, random_state=42
        )
    else:
        X_train, y_train = X_train_full, y_train_full

    # ── Train Models ───────────────────────────────────────────
    train_start = time.time()
    best_model, best_name, best_params, best_score, all_results = train_best_model(X_train, y_train)
    train_end = time.time()

    # ── Evaluate on Test Set ───────────────────────────────────
    inf_start = time.time()
    metrics = evaluate_model(best_model, X_test, y_test, OUTPUT_DIR)
    inf_end = time.time()

    # ── Calibration ────────────────────────────────────────────
    final_model, calibration_improved, final_brier, final_logloss = try_calibration(
        best_model, X_train, y_train, X_test, y_test, OUTPUT_DIR
    )

    if calibration_improved:
        # Re-evaluate with calibrated model
        metrics = evaluate_model(final_model, X_test, y_test, OUTPUT_DIR)
        metrics['Calibration_Applied'] = True
    else:
        metrics['Calibration_Applied'] = False
        final_model = best_model

    metrics['Brier_Score'] = round(final_brier, 4)
    metrics['Log_Loss'] = round(final_logloss, 4)

    # ── Save Artifacts ─────────────────────────────────────────
    logging.info("Saving artifacts...")
    with open(OUTPUT_DIR / 'best_model.pkl', 'wb') as f:
        pickle.dump(final_model, f)

    with open(OUTPUT_DIR / 'label_encoder.pkl', 'wb') as f:
        pickle.dump(encoders, f)

    with open(OUTPUT_DIR / 'feature_columns.pkl', 'wb') as f:
        pickle.dump(feature_columns, f)

    # ── Prediction Test ────────────────────────────────────────
    logging.info("Running prediction test...")
    try:
        sample_df = pd.read_csv(DATA_PATH, nrows=5)
        sample_probs = predict_win_probability(sample_df, OUTPUT_DIR)
        for i, prob in enumerate(sample_probs):
            logging.info(f"  Ball {i+1}: Win Probability = {prob:.2f}%")
    except Exception as e:
        logging.warning(f"Prediction test skipped: {e}")

    # ── Build Report ───────────────────────────────────────────
    report = {
        "Training_Samples": len(X_train),
        "Validation_Samples": len(X_val),
        "Testing_Samples": len(X_test),
        "Total_Features_Used": len(feature_columns),
        "Dropped_Correlated_Features": dropped_cols,
        "Features_Used": feature_columns,
        "Algorithms_Tested": list(all_results.keys()),
        "Algorithm_Scores": {k: round(v['score'], 4) for k, v in all_results.items()},
        "Best_Algorithm": best_name,
        "Best_Hyperparameters": best_params,
        "Cross_Validation_ROC_AUC": round(best_score, 4),
        "Calibration_Applied": calibration_improved,
        "Accuracy": metrics['Accuracy'],
        "Precision": metrics['Precision'],
        "Recall": metrics['Recall'],
        "F1_Score": metrics['F1_Score'],
        "ROC_AUC": metrics['ROC_AUC'],
        "PR_AUC": metrics['PR_AUC'],
        "Log_Loss": metrics['Log_Loss'],
        "Brier_Score": metrics['Brier_Score'],
        "Training_Time_Seconds": round(train_end - train_start, 2),
        "Inference_Time_Seconds": round(inf_end - inf_start, 2),
        "Artifact_Locations": {
            "Model": str(OUTPUT_DIR / 'best_model.pkl'),
            "Label_Encoders": str(OUTPUT_DIR / 'label_encoder.pkl'),
            "Feature_Columns": str(OUTPUT_DIR / 'feature_columns.pkl'),
            "Metrics": str(OUTPUT_DIR / 'model_metrics.json'),
            "Feature_Importance": str(OUTPUT_DIR / 'feature_importance.csv'),
            "Classification_Report": str(OUTPUT_DIR / 'classification_report.txt'),
            "Confusion_Matrix": str(OUTPUT_DIR / 'confusion_matrix.png'),
            "ROC_Curve": str(OUTPUT_DIR / 'roc_curve.png'),
            "Calibration_Curve": str(OUTPUT_DIR / 'calibration_curve.png')
        }
    }

    with open(OUTPUT_DIR / 'win_training_report.json', 'w') as f:
        json.dump(report, f, indent=4)

    # Save model_metrics.json with final values
    with open(OUTPUT_DIR / 'model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)

    logging.info("=" * 60)
    logging.info("Phase 3B: Win Probability Prediction — COMPLETE")
    logging.info("=" * 60)
    print(json.dumps(report, indent=4))

    total_time = round(time.time() - start_time, 2)
    logging.info(f"Total pipeline time: {total_time}s")


if __name__ == "__main__":
    main()
