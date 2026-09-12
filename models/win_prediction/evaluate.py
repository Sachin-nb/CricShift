import pandas as pd
import numpy as np
import logging
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, log_loss, brier_score_loss,
    confusion_matrix, classification_report,
    roc_curve, auc, precision_recall_curve
)
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from pathlib import Path


def evaluate_model(model, X_test, y_test, output_dir: Path):
    """Evaluates the model and saves all artifacts."""
    logging.info("Evaluating model...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Core metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc = roc_auc_score(y_test, y_proba)
    pr_auc = average_precision_score(y_test, y_proba)
    logloss = log_loss(y_test, y_proba)
    brier = brier_score_loss(y_test, y_proba)

    metrics = {
        'Accuracy': round(acc, 4),
        'Precision': round(prec, 4),
        'Recall': round(rec, 4),
        'F1_Score': round(f1, 4),
        'ROC_AUC': round(roc, 4),
        'PR_AUC': round(pr_auc, 4),
        'Log_Loss': round(logloss, 4),
        'Brier_Score': round(brier, 4)
    }

    # Save model_metrics.json
    with open(output_dir / 'model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)

    # Classification report
    cr = classification_report(y_test, y_pred, target_names=['Loss', 'Win'])
    with open(output_dir / 'classification_report.txt', 'w') as f:
        f.write(cr)
    logging.info(f"\n{cr}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Loss', 'Win'], yticklabels=['Loss', 'Win'])
    plt.title('Win Probability Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(output_dir / 'confusion_matrix.png', dpi=150)
    plt.close()

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, lw=2, label=f'ROC (AUC = {roc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Win Probability Prediction')
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(output_dir / 'roc_curve.png', dpi=150)
    plt.close()

    # Calibration Curve
    prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=10, strategy='uniform')
    plt.figure(figsize=(8, 6))
    plt.plot(prob_pred, prob_true, marker='o', lw=2, label='Model')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
    plt.xlabel('Mean Predicted Probability')
    plt.ylabel('Fraction of Positives')
    plt.title('Calibration Curve - Win Probability')
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(output_dir / 'calibration_curve.png', dpi=150)
    plt.close()

    # Feature importance
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        feature_names = X_test.columns
        fi_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        fi_df = fi_df.sort_values(by='Importance', ascending=False)
        fi_df.to_csv(output_dir / 'feature_importance.csv', index=False)

        # Plot top 20
        top20 = fi_df.head(20)
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(top20) - 1, -1, -1), top20['Importance'].values, color='steelblue')
        plt.yticks(range(len(top20) - 1, -1, -1), top20['Feature'].values)
        plt.xlabel('Importance')
        plt.title('Top 20 Feature Importances - Win Probability')
        plt.tight_layout()
        plt.savefig(output_dir / 'feature_importance_top20.png', dpi=150)
        plt.close()
    elif hasattr(model, 'coef_'):
        # For LogisticRegression
        importances = np.abs(model.coef_[0])
        feature_names = X_test.columns
        fi_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        fi_df = fi_df.sort_values(by='Importance', ascending=False)
        fi_df.to_csv(output_dir / 'feature_importance.csv', index=False)

    return metrics


def try_calibration(model, X_train, y_train, X_test, y_test, output_dir: Path):
    """Attempts probability calibration and returns improved model if better."""
    logging.info("Attempting probability calibration with CalibratedClassifierCV...")

    try:
        # Get baseline Brier and Log Loss
        y_proba_base = model.predict_proba(X_test)[:, 1]
        brier_base = brier_score_loss(y_test, y_proba_base)
        logloss_base = log_loss(y_test, y_proba_base)

        # Calibrate using sigmoid (Platt scaling)
        cal_model = CalibratedClassifierCV(model, method='sigmoid', cv=3)
        cal_model.fit(X_train, y_train)

        y_proba_cal = cal_model.predict_proba(X_test)[:, 1]
        brier_cal = brier_score_loss(y_test, y_proba_cal)
        logloss_cal = log_loss(y_test, y_proba_cal)

        logging.info(f"Before calibration: Brier={brier_base:.4f}, LogLoss={logloss_base:.4f}")
        logging.info(f"After calibration:  Brier={brier_cal:.4f}, LogLoss={logloss_cal:.4f}")

        improved = brier_cal < brier_base or logloss_cal < logloss_base

        if improved:
            logging.info("Calibration IMPROVED predictions. Using calibrated model.")
            # Re-plot calibration curve
            prob_true, prob_pred = calibration_curve(y_test, y_proba_cal, n_bins=10, strategy='uniform')
            plt.figure(figsize=(8, 6))
            plt.plot(prob_pred, prob_true, marker='o', lw=2, label='Calibrated Model')
            plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly Calibrated')
            plt.xlabel('Mean Predicted Probability')
            plt.ylabel('Fraction of Positives')
            plt.title('Calibration Curve (After Calibration)')
            plt.legend(loc='upper left')
            plt.tight_layout()
            plt.savefig(output_dir / 'calibration_curve.png', dpi=150)
            plt.close()
            return cal_model, True, brier_cal, logloss_cal
        else:
            logging.info("Calibration did NOT improve. Keeping original model.")
            return model, False, brier_base, logloss_base

    except Exception as e:
        logging.warning(f"Calibration failed: {e}. Keeping original model.")
        y_proba_base = model.predict_proba(X_test)[:, 1]
        return model, False, brier_score_loss(y_test, y_proba_base), log_loss(y_test, y_proba_base)
