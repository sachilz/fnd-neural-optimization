import numpy as np
import scipy.sparse as sp
import torch
from torch.utils.data import Dataset

class SparseTFIDFDataset(Dataset):
    """
    Memory-efficient PyTorch Dataset for sparse TF-IDF matrices.
    Loads sparse npz files and yields dense vectors on-the-fly.
    """
    def __init__(self, X_path: str, y_path: str):
        self.X = sp.load_npz(X_path)
        self.y = torch.tensor(np.load(y_path), dtype=torch.long)
        
    def __len__(self):
        return self.X.shape[0]
        
    def __getitem__(self, idx):
        # Slice sparse row, convert to dense, and remove singleton dimension
        row = self.X[idx].toarray().squeeze(0)
        return torch.tensor(row, dtype=torch.float32), self.y[idx]
