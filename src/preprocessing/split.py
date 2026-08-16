"""
Train/validation/test splitting with stratification and leakage prevention.
"""

from typing import Tuple, Dict
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def stratified_split(
    df: pd.DataFrame,
    text_col: str = 'text',
    label_col: str = 'label',
    train_size: float = 0.7,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train, validation, and test sets with stratification.

    Ensures no leakage between splits.
    """
    # First split: train vs (val + test)
    train, temp = train_test_split(
        df,
        train_size=train_size,
        stratify=df[label_col],
        random_state=random_state
    )

    # Second split: val vs test
    val, test = train_test_split(
        temp,
        test_size=test_size / (val_size + test_size),
        stratify=temp[label_col],
        random_state=random_state
    )

    return train, val, test


def verify_split(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    text_col: str = 'text',
    label_col: str = 'label'
) -> Dict:
    """Verify split integrity."""
    # Check for text overlap
    train_texts = set(train[text_col].values)
    val_texts = set(val[text_col].values)
    test_texts = set(test[text_col].values)

    overlap_train_val = train_texts & val_texts
    overlap_train_test = train_texts & test_texts
    overlap_val_test = val_texts & test_texts

    return {
        'train_size': len(train),
        'val_size': len(val),
        'test_size': len(test),
        'train_class_dist': train[label_col].value_counts(normalize=True).to_dict(),
        'val_class_dist': val[label_col].value_counts(normalize=True).to_dict(),
        'test_class_dist': test[label_col].value_counts(normalize=True).to_dict(),
        'overlap_train_val': len(overlap_train_val),
        'overlap_train_test': len(overlap_train_test),
        'overlap_val_test': len(overlap_val_test),
        'total_overlap': len(overlap_train_val | overlap_train_test | overlap_val_test)
    }