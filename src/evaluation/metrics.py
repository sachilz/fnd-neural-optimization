import json
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns
import os

def evaluate_model(y_true, y_pred, y_prob=None, output_dir=None, prefix=""):
    """
    Evaluate model predictions and save metrics/confusion matrix.
    """
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    
    metrics = {
        'accuracy': float(acc),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1)
    }
    
    if y_prob is not None:
        try:
            auc = roc_auc_score(y_true, y_prob)
            metrics['roc_auc'] = float(auc)
        except ValueError:
            pass # Handle single class batches if any
            
    cm = confusion_matrix(y_true, y_pred)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        # Plot confusion matrix
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Fake (0)', 'True (1)'], yticklabels=['Fake (0)', 'True (1)'])
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.title(f'{prefix} Confusion Matrix')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{prefix}_confusion_matrix.png'))
        plt.close()
        
    return metrics
