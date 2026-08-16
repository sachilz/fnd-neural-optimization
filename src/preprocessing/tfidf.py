"""
TF-IDF vectorization with strict leakage prevention.

- Fit ONLY on training data
- Transform validation and test data using the fitted vectorizer
"""

from typing import Tuple, Dict
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def create_tfidf_vectorizer(max_features: int = 5000) -> TfidfVectorizer:
    """Create a TF-IDF vectorizer with fixed parameters."""
    return TfidfVectorizer(
        max_features=max_features,
        stop_words='english',
        lowercase=True,
        ngram_range=(1, 2)
    )


def fit_transform_tfidf(
    train_texts: pd.Series,
    val_texts: pd.Series,
    test_texts: pd.Series,
    max_features: int = 5000
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, TfidfVectorizer]:
    """
    Fit TF-IDF on training data and transform validation/test data.

    Returns:
        X_train, X_val, X_test, vectorizer
    """
    vectorizer = create_tfidf_vectorizer(max_features)

    # Fit on training data ONLY
    X_train = vectorizer.fit_transform(train_texts).astype(np.float32)

    # Transform validation and test data using the fitted vectorizer
    X_val = vectorizer.transform(val_texts).astype(np.float32)
    X_test = vectorizer.transform(test_texts).astype(np.float32)

    return X_train, X_val, X_test, vectorizer


def verify_tfidf(
    X_train: np.ndarray,
    X_val: np.ndarray,
    X_test: np.ndarray,
    vectorizer: TfidfVectorizer
) -> Dict:
    """Verify TF-IDF integrity."""
    return {
        'X_train_shape': X_train.shape,
        'X_val_shape': X_val.shape,
        'X_test_shape': X_test.shape,
        'vocabulary_size': len(vectorizer.vocabulary_),
        'max_features': vectorizer.max_features,
        'ngram_range': vectorizer.ngram_range,
        'train_non_zero': X_train.nnz,
        'val_non_zero': X_val.nnz,
        'test_non_zero': X_test.nnz,
        'train_density': X_train.nnz / (X_train.shape[0] * X_train.shape[1]),
        'val_density': X_val.nnz / (X_val.shape[0] * X_val.shape[1]),
        'test_density': X_test.nnz / (X_test.shape[0] * X_test.shape[1])
    }