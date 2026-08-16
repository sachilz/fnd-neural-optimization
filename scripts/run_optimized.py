import os
import sys
import json
import torch
from torch.utils.data import DataLoader
import numpy as np

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.seed import set_seed
set_seed(42)
from data.dataset import SparseTFIDFDataset
from models.baseline import FakeNewsMLP
from models.train import train_model
from evaluation.metrics import evaluate_model
def get_predictions(model, loader, device):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)[:, 1]
            _, preds = torch.max(outputs, 1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())
            
    return np.array(all_labels), np.array(all_preds), np.array(all_probs)

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(base_dir, 'data', 'processed')
    results_dir = os.path.join(base_dir, 'results')
    models_dir = os.path.join(base_dir, 'models')
    
    # Load dataset metadata
    with open(os.path.join(data_dir, 'preprocessing_metadata.json'), 'r') as f:
        meta = json.load(f)
        
    # Load PSO best params
    with open(os.path.join(results_dir, 'metrics', 'pso_best_params.json'), 'r') as f:
        best_params = json.load(f)
        
    input_dim = meta['max_features']
    
    print("Loading datasets...")
    train_dataset = SparseTFIDFDataset(os.path.join(data_dir, 'X_train.npz'), os.path.join(data_dir, 'y_train.npy'))
    val_dataset = SparseTFIDFDataset(os.path.join(data_dir, 'X_val.npz'), os.path.join(data_dir, 'y_val.npy'))
    test_dataset = SparseTFIDFDataset(os.path.join(data_dir, 'X_test.npz'), os.path.join(data_dir, 'y_test.npy'))
    
    batch_size = 64
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    print(f"Training Optimized Model with parameters: {best_params}")
    model = FakeNewsMLP(
        input_dim=input_dim, 
        hidden_dim=best_params['hidden_dim'], 
        dropout_rate=best_params['dropout_rate']
    )
    
    model, history, train_time = train_model(
        model, train_loader, val_loader, 
        epochs=10, 
        lr=best_params['learning_rate'], 
        device=device
    )
    
    # Save model
    model_path = os.path.join(models_dir, 'optimized_mlp.pth')
    torch.save(model.state_dict(), model_path)
    print(f"Optimized model saved to {model_path}")
    
    # Evaluate on Validation Set
    print("\nEvaluating Optimized Model on Validation Set...")
    val_true, val_pred, val_prob = get_predictions(model, val_loader, device)
    val_metrics = evaluate_model(
        val_true, val_pred, val_prob, 
        output_dir=os.path.join(results_dir, 'figures', 'evaluation'),
        prefix="optimized_val"
    )
    
    # Evaluate on Test Set
    print("Evaluating Optimized Model on Test Set...")
    test_true, test_pred, test_prob = get_predictions(model, test_loader, device)
    test_metrics = evaluate_model(
        test_true, test_pred, test_prob, 
        output_dir=os.path.join(results_dir, 'figures', 'evaluation'),
        prefix="optimized_test"
    )
    
    # Save metrics
    results = {
        'training_time_seconds': float(train_time),
        'hyperparameters': best_params,
        'history': history,
        'validation_metrics': val_metrics,
        'test_metrics': test_metrics
    }
    
    metrics_path = os.path.join(results_dir, 'metrics', 'optimized_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Optimized Results saved to {metrics_path}")
    print(f"\nOptimized Test Accuracy: {test_metrics['accuracy']:.4f}")

if __name__ == '__main__':
    main()
