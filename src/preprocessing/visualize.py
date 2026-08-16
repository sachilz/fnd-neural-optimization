"""
Visualizations for preprocessing results.
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_class_distribution(df: pd.DataFrame, label_col: str = 'label', output_dir: str = 'results/figures/preprocessing') -> None:
    """Plot class distribution."""
    os.makedirs(output_dir, exist_ok=True)

    plt.figure(figsize=(8, 5))
    ax = sns.countplot(x=label_col, data=df)
    ax.set_title('Class Distribution (Fake vs Real News)')
    ax.set_xlabel('Label')
    ax.set_ylabel('Count')
    ax.set_xticklabels(['Fake (0)', 'Real (1)'])

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'class_distribution.png'))
    plt.close()


def plot_text_length(df: pd.DataFrame, text_col: str = 'text', output_dir: str = 'results/figures/preprocessing') -> None:
    """Plot text length distribution."""
    os.makedirs(output_dir, exist_ok=True)

    df['text_length'] = df[text_col].apply(len)

    plt.figure(figsize=(10, 6))
    sns.histplot(df, x='text_length', hue='label', bins=50, kde=True, alpha=0.6)
    plt.title('Text Length Distribution')
    plt.xlabel('Text Length (characters)')
    plt.ylabel('Count')
    plt.legend(title='Label', labels=['Fake (0)', 'Real (1)'])

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'text_length_distribution.png'))
    plt.close()


def plot_split_distribution(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, label_col: str = 'label', output_dir: str = 'results/figures/preprocessing') -> None:
    """Plot train/validation/test class distribution."""
    os.makedirs(output_dir, exist_ok=True)

    # Combine splits with a 'split' column
    train['split'] = 'Train'
    val['split'] = 'Validation'
    test['split'] = 'Test'
    combined = pd.concat([train, val, test])

    plt.figure(figsize=(10, 6))
    sns.countplot(x='split', hue=label_col, data=combined)
    plt.title('Class Distribution Across Splits')
    plt.xlabel('Split')
    plt.ylabel('Count')
    plt.legend(title='Label', labels=['Fake (0)', 'Real (1)'])

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'split_class_distribution.png'))
    plt.close()