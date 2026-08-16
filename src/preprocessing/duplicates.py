"""
Duplicate detection and handling for news articles.

Handles:
- Exact duplicate rows
- Duplicate article text
- Conflicting labels (same text, different label)
"""

from typing import List, Tuple, Dict
import pandas as pd


def find_duplicates(df: pd.DataFrame, text_col: str = 'text', label_col: str = 'label') -> Dict[str, List[Tuple[int, int]]]:
    """
    Find duplicate texts and their indices.

    Returns:
        dict: {
            'exact_duplicates': [(index1, index2), ...],
            'conflicting_labels': [(index1, index2), ...]
        }
    """
    # Find duplicate texts
    duplicates = df.duplicated(subset=[text_col], keep=False)
    duplicate_texts = df[duplicates][text_col].values

    # Group by text
    text_to_indices = {}
    for idx, text in enumerate(df[text_col].values):
        if text in duplicate_texts:
            if text not in text_to_indices:
                text_to_indices[text] = []
            text_to_indices[text].append(idx)

    # Classify duplicates
    exact_duplicates = []
    conflicting_labels = []

    for text, indices in text_to_indices.items():
        if len(indices) < 2:
            continue

        # Check if all labels are the same
        labels = df.iloc[indices][label_col].values
        if len(set(labels)) == 1:
            # Exact duplicates (same text, same label)
            for i in range(len(indices) - 1):
                exact_duplicates.append((indices[i], indices[i + 1]))
        else:
            # Conflicting labels (same text, different label)
            for i in range(len(indices) - 1):
                conflicting_labels.append((indices[i], indices[i + 1]))

    return {
        'exact_duplicates': exact_duplicates,
        'conflicting_labels': conflicting_labels
    }


def remove_duplicates(df: pd.DataFrame, text_col: str = 'text', label_col: str = 'label', strategy: str = 'keep_first') -> pd.DataFrame:
    """
    Remove duplicate rows based on text and label.

    Args:
        strategy: 'keep_first' (default), 'keep_last', or 'drop_all'
    """
    if strategy == 'drop_all':
        # Remove all duplicates (including conflicting labels)
        return df.drop_duplicates(subset=[text_col], keep=False)
    else:
        # Remove duplicates, keeping one copy
        keep_param = 'first' if strategy == 'keep_first' else 'last'
        return df.drop_duplicates(subset=[text_col], keep=keep_param)


def report_duplicates(df: pd.DataFrame, text_col: str = 'text', label_col: str = 'label') -> Dict:
    """Generate a duplicate report."""
    duplicates = find_duplicates(df, text_col, label_col)

    return {
        'total_rows': len(df),
        'exact_duplicate_count': len(duplicates['exact_duplicates']),
        'conflicting_label_count': len(duplicates['conflicting_labels']),
        'unique_texts': df[text_col].nunique(),
        'duplicate_texts': len(set([df.iloc[i][text_col] for i, _ in duplicates['exact_duplicates'] + duplicates['conflicting_labels']]))
    }