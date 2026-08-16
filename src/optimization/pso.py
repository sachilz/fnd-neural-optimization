import numpy as np
import pyswarms as ps
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score
import os

def pso_fitness_function(
    particles, 
    train_dataset, 
    val_dataset, 
    input_dim, 
    device,
    epochs_per_eval=3
):
    """
    Fitness function for PSO.
    particles: numpy array of shape (n_particles, dimensions)
    dimensions: [hidden_dim, learning_rate, dropout_rate]
    
    Returns array of fitness scores (negative validation accuracy to minimize).
    """
    from models.baseline import FakeNewsMLP
    from models.train import train_model
    from data.dataset import SparseTFIDFDataset
    
    n_particles = particles.shape[0]
    fitness_scores = np.zeros(n_particles)
    
    # We use a smaller batch size and fewer epochs for fast fitness evaluation
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=256, shuffle=False, num_workers=2)
    
    for i in range(n_particles):
        # Decode particle
        # hidden_dim: continuous mapped to int [32, 256]
        # learning_rate: continuous [0.0001, 0.01] (using log scale mapping or direct)
        # dropout_rate: continuous [0.1, 0.6]
        
        hidden_dim = int(particles[i, 0])
        lr = particles[i, 1]
        dropout = particles[i, 2]
        
        print(f"Evaluating Particle {i+1}/{n_particles} | hidden_dim={hidden_dim}, lr={lr:.5f}, dropout={dropout:.3f}")
        
        model = FakeNewsMLP(
            input_dim=input_dim, 
            hidden_dim=hidden_dim, 
            dropout_rate=dropout
        )
        
        trained_model, history, _ = train_model(
            model, 
            train_loader, 
            val_loader, 
            epochs=epochs_per_eval, 
            lr=lr, 
            device=device
        )
        
        # We want to maximize validation accuracy, so we return negative accuracy
        # The best model during training is loaded back by train_model
        val_acc = max(history['val_acc'])
        fitness_scores[i] = -val_acc
        
    return fitness_scores

def run_pso_optimization(
    train_dataset,
    val_dataset,
    input_dim,
    device,
    n_particles=10,
    iters=5
):
    """
    Run the PSO optimization.
    """
    # Bounds: [hidden_dim, lr, dropout]
    max_bound = np.array([256.99, 0.01, 0.6])
    min_bound = np.array([32.0, 0.0001, 0.1])
    bounds = (min_bound, max_bound)
    
    options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}
    
    optimizer = ps.single.GlobalBestPSO(
        n_particles=n_particles, 
        dimensions=3, 
        options=options, 
        bounds=bounds
    )
    
    # Define the objective function wrapper
    def objective_func(particles):
        return pso_fitness_function(
            particles, 
            train_dataset, 
            val_dataset, 
            input_dim, 
            device,
            epochs_per_eval=3
        )
        
    cost, pos = optimizer.optimize(objective_func, iters=iters)
    
    best_params = {
        'hidden_dim': int(pos[0]),
        'learning_rate': float(pos[1]),
        'dropout_rate': float(pos[2]),
        'best_val_accuracy': float(-cost)
    }
    
    return best_params
