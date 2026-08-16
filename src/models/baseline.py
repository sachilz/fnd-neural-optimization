import torch.nn as nn

class FakeNewsMLP(nn.Module):
    """
    Baseline Multi-Layer Perceptron (MLP) for Fake News Detection.
    """
    def __init__(self, input_dim: int = 5000, hidden_dim: int = 128, dropout_rate: float = 0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim // 2, 2)
        )
        
    def forward(self, x):
        return self.net(x)
