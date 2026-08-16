import os
import sys
import json
import torch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.seed import set_seed
set_seed(42)
from data.dataset import SparseTFIDFDataset
from optimization.pso import run_pso_optimization

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(base_dir, 'data', 'processed')
    results_dir = os.path.join(base_dir, 'results', 'metrics')
    os.makedirs(results_dir, exist_ok=True)
    
    # Load dataset metadata
    with open(os.path.join(data_dir, 'preprocessing_metadata.json'), 'r') as f:
        meta = json.load(f)
        
    input_dim = meta['max_features']
    
    print("Loading datasets for PSO...")
    train_dataset = SparseTFIDFDataset(os.path.join(data_dir, 'X_train.npz'), os.path.join(data_dir, 'y_train.npy'))
    val_dataset = SparseTFIDFDataset(os.path.join(data_dir, 'X_val.npz'), os.path.join(data_dir, 'y_val.npy'))
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Run PSO
    # For a real academic project, n_particles and iters should be higher (e.g. 10 particles, 10 iters)
    # Here we use 5 particles and 3 iterations to save time but prove the concept works.
    print("Starting PSO Optimization (this will take a while)...")
    best_params = run_pso_optimization(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        input_dim=input_dim,
        device=device,
        n_particles=20,
        iters=10
    )
    
    print(f"\nOptimization complete!")
    print(f"Best hyperparameters: {json.dumps(best_params, indent=2)}")
    
    # Save best parameters
    params_path = os.path.join(results_dir, 'pso_best_params.json')
    with open(params_path, 'w') as f:
        json.dump(best_params, f, indent=2)
        
    print(f"Best parameters saved to {params_path}")

if __name__ == '__main__':
    main()
