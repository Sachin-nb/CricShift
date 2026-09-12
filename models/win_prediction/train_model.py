import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False


def get_models():
    """Returns dict of (model, param_grid) for all available algorithms."""
    models = {
        'LogisticRegression': (LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'), {
            'C': [0.01, 0.1, 1, 10, 100],
            'solver': ['lbfgs', 'saga'],
            'penalty': ['l2']
        }),
        'RandomForest': (RandomForestClassifier(random_state=42, n_jobs=-1, class_weight='balanced'), {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', 0.3]
        }),
        'ExtraTrees': (ExtraTreesClassifier(random_state=42, n_jobs=-1, class_weight='balanced'), {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', 0.3]
        }),
        'GradientBoosting': (GradientBoostingClassifier(random_state=42), {
            'n_estimators': [100, 200, 300],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2],
            'subsample': [0.8, 1.0]
        })
    }

    if HAS_XGB:
        models['XGBoost'] = (XGBClassifier(random_state=42, eval_metric='logloss', n_jobs=-1), {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [3, 5, 7, 9],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0],
            'scale_pos_weight': [1, 1.5]
        })

    if HAS_LGBM:
        models['LightGBM'] = (LGBMClassifier(random_state=42, n_jobs=-1, verbose=-1, class_weight='balanced'), {
            'n_estimators': [100, 200, 300, 500],
            'max_depth': [3, 5, 7, -1],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'num_leaves': [31, 63, 127],
            'subsample': [0.8, 1.0]
        })

    if HAS_CATBOOST:
        models['CatBoost'] = (CatBoostClassifier(random_state=42, thread_count=-1, verbose=0, auto_class_weights='Balanced'), {
            'iterations': [100, 200],
            'depth': [4, 6, 8],
            'learning_rate': [0.05, 0.1, 0.2],
            'l2_leaf_reg': [1, 3, 5]
        })

    return models


def train_best_model(X_train, y_train):
    """Trains all models with RandomizedSearchCV and returns the best one by ROC-AUC."""
    from sklearn.utils.class_weight import compute_sample_weight

    models = get_models()
    results = {}
    best_model = None
    best_score = 0
    best_name = ""
    best_params = {}

    sample_weights = compute_sample_weight('balanced', y_train)

    for name, (model, params) in models.items():
        logging.info(f"Training and tuning {name}...")
        try:
            search = RandomizedSearchCV(
                model, params,
                n_iter=20, cv=5,
                scoring='roc_auc',
                n_jobs=-1,
                random_state=42
            )

            if name in ('XGBoost', 'GradientBoosting'):
                search.fit(X_train, y_train, sample_weight=sample_weights)
            else:
                search.fit(X_train, y_train)

            score = search.best_score_
            results[name] = {
                'score': score,
                'params': search.best_params_
            }
            logging.info(f"{name} Best CV ROC-AUC: {score:.4f}")

            if score > best_score:
                best_score = score
                best_model = search.best_estimator_
                best_name = name
                best_params = search.best_params_

        except Exception as e:
            logging.error(f"Error training {name}: {e}")

    logging.info(f"Best Model: {best_name} (ROC-AUC: {best_score:.4f})")
    logging.info(f"Best Params: {best_params}")

    return best_model, best_name, best_params, best_score, results
