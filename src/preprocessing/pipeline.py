"""
Complete preprocessing pipeline from raw CSV to final TF-IDF matrices.
"""

import json
import os
from typing import Dict, Tuple
import numpy as np
import pandas as pd

from .clean import clean_texts
from .duplicates import find_duplicates, remove_duplicates, report_duplicates
from .split import stratified_split, verify_split
from .tfidf import fit_transform_tfidf, verify_tfidf


def load_raw_data(fake_path: str, true_path: str) -> pd.DataFrame:
    """Load and combine raw CSV files."""
    fake = pd.read_csv(fake_path)
    true = pd.read_csv(true_path)

    # Add labels
    fake['label'] = 0
    true['label'] = 1

    # Combine
    df = pd.concat([fake, true], ignore_index=True)

    return df


def preprocess_pipeline(
    fake_path: str,
    true_path: str,
    output_dir: str = 'data',
    max_features: int = 5000,
    random_state: int = 42
) -> Dict:
    """
    Complete preprocessing pipeline.

    Returns:
        metadata: Dict of preprocessing statistics
    """
    # Load raw data
    df = load_raw_data(fake_path, true_path)

    # Initial report
    initial_stats = {
        'original_fake_rows': len(df[df['label'] == 0]),
        'original_true_rows': len(df[df['label'] == 1]),
        'original_total_rows': len(df),
        'original_empty_text': (df['text'].str.strip() == '').sum()
    }

    # Clean text
    df['text'] = clean_texts(df['text'].astype(str))

    # Remove empty text
    empty_before = (df['text'] == '').sum()
    df = df[df['text'] != '']
    empty_after = (df['text'] == '').sum()

    # Duplicate handling
    duplicates_report = report_duplicates(df)
    df = remove_duplicates(df, strategy='keep_first')

    # Final dataset
    final_stats = {
        'final_total_rows': len(df),
        'final_fake_rows': len(df[df['label'] == 0]),
        'final_true_rows': len(df[df['label'] == 1]),
        'final_empty_text': (df['text'] == '').sum()
    }

    # Stratified split
    train, val, test = stratified_split(df, random_state=random_state)

    # TF-IDF vectorization (FIT ON TRAIN ONLY)
    X_train, X_val, X_test, vectorizer = fit_transform_tfidf(
        train['text'],
        val['text'],
        test['text'],
        max_features=max_features
    )

    # Save processed data
    os.makedirs(output_dir, exist_ok=True)

    # Save sparse matrices properly
    from scipy.sparse import save_npz
    save_npz(os.path.join(output_dir, 'X_train.npz'), X_train)
    save_npz(os.path.join(output_dir, 'X_val.npz'), X_val)
    save_npz(os.path.join(output_dir, 'X_test.npz'), X_test)

    # Save labels
    np.save(os.path.join(output_dir, 'y_train.npy'), train['label'].values)
    np.save(os.path.join(output_dir, 'y_val.npy'), val['label'].values)
    np.save(os.path.join(output_dir, 'y_test.npy'), test['label'].values)

    # Save vectorizer
    import joblib
    joblib.dump(vectorizer, os.path.join(output_dir, 'tfidf_vectorizer.pkl'))

    # Verify splits
    split_report = verify_split(train, val, test)
    tfidf_report = verify_tfidf(X_train, X_val, X_test, vectorizer)

    # Create metadata
    metadata = {
        'random_seed': random_state,
        **{k: int(v) if isinstance(v, (np.int64, np.int32)) else v for k, v in initial_stats.items()},
        'empty_text_removed': int(empty_before - empty_after),
        **{k: int(v) if isinstance(v, (np.int64, np.int32)) else v for k, v in duplicates_report.items()},
        **{k: int(v) if isinstance(v, (np.int64, np.int32)) else v for k, v in final_stats.items()},
        **{k: {kk: float(vv) if isinstance(vv, (np.float64, np.float32)) else vv for kk, vv in v.items()} if isinstance(v, dict) else v for k, v in split_report.items()},
        **{k: int(v) if isinstance(v, (np.int64, np.int32)) else v for k, v in tfidf_report.items()},
        'output_files': {
            'X_train': os.path.join(output_dir, 'X_train.npz'),
            'X_val': os.path.join(output_dir, 'X_val.npz'),
            'X_test': os.path.join(output_dir, 'X_test.npz'),
            'y_train': os.path.join(output_dir, 'y_train.npy'),
            'y_val': os.path.join(output_dir, 'y_val.npy'),
            'y_test': os.path.join(output_dir, 'y_test.npy'),
            'tfidf_vectorizer': os.path.join(output_dir, 'tfidf_vectorizer.pkl')
        }
    }

    # Save metadata
    with open(os.path.join(output_dir, 'preprocessing_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata