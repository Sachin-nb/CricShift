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
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, auc
)
from pathlib import Path


def evaluate_model(model, X_test, y_test, output_dir: Path):
    """Evaluates the model and saves all artifacts."""
    logging.info("Evaluating model...")
    y_pred = model.predict(X_test)
    
    # Core metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
    rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    per_class_recall = recall_score(y_test, y_pred, average=None, zero_division=0).tolist()
    
    # ROC AUC
    roc_auc = None
    try:
        y_proba = model.predict_proba(X_test)
        roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr')
        
        # Plot ROC curve per class
        n_classes = y_proba.shape[1]
        plt.figure(figsize=(8, 6))
        for i in range(n_classes):
            y_test_bin = (y_test == i).astype(int)
            fpr, tpr, _ = roc_curve(y_test_bin, y_proba[:, i])
            roc_auc_i = auc(fpr, tpr)
            class_names = {0: 'Negative', 1: 'Neutral', 2: 'Positive'}
            label = class_names.get(i, f'Class {i}')
            plt.plot(fpr, tpr, lw=2, label=f'{label} (AUC = {roc_auc_i:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve - Momentum Shift Detection')
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(output_dir / 'roc_curve.png', dpi=150)
        plt.close()
    except Exception as e:
        logging.warning(f"Could not calculate ROC AUC: {e}")
    
    # Build metrics dict
    metrics = {
        'Accuracy': round(acc, 4),
        'Precision': round(prec, 4),
        'Recall': round(rec, 4),
        'F1_Score': round(f1, 4),
        'Weighted_F1': round(weighted_f1, 4),
        'ROC_AUC': round(roc_auc, 4) if roc_auc is not None else "N/A",
        'Per_Class_Recall': {str(i): round(r, 4) for i, r in enumerate(per_class_recall)}
    }
    with open(output_dir / 'model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
    
    # Classification report
    cr = classification_report(y_test, y_pred, target_names=['Negative', 'Neutral', 'Positive'])
    with open(output_dir / 'classification_report.txt', 'w') as f:
        f.write(cr)
    logging.info(f"\n{cr}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Negative', 'Neutral', 'Positive'],
                yticklabels=['Negative', 'Neutral', 'Positive'])
    plt.title('Momentum Shift Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(output_dir / 'confusion_matrix.png', dpi=150)
    plt.close()
    
    # Feature importance
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        feature_names = X_test.columns
        fi_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        fi_df = fi_df.sort_values(by='Importance', ascending=False)
        fi_df.to_csv(output_dir / 'feature_importance.csv', index=False)
    
    return metrics
