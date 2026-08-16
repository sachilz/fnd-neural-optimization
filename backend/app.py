import os
import sys
import json
import torch
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from preprocessing.clean import clean_text
from models.baseline import FakeNewsMLP

app = FastAPI(title="Fake News Detection API")

# Add CORS so the frontend can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state to cache models and vectorizers
STATE = {
    "vectorizer": None,
    "input_dim": None,
    "device": None,
    "models": {}
}

class PredictRequest(BaseModel):
    text: str
    model_choice: str  # '1' for Baseline, '2' for PSO Optimized

@app.on_event("startup")
def load_environment():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(base_dir, 'data', 'processed')
    models_dir = os.path.join(base_dir, 'models')
    
    try:
        # Load metadata
        with open(os.path.join(data_dir, 'preprocessing_metadata.json'), 'r') as f:
            meta = json.load(f)
        STATE["input_dim"] = meta['max_features']
        
        # Load vectorizer
        STATE["vectorizer"] = joblib.load(os.path.join(data_dir, 'tfidf_vectorizer.pkl'))
        STATE["device"] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Pre-load Baseline
        baseline = FakeNewsMLP(input_dim=STATE["input_dim"], hidden_dim=128, dropout_rate=0.5)
        baseline.load_state_dict(torch.load(os.path.join(models_dir, 'baseline_mlp.pth'), map_location=STATE["device"]))
        baseline.to(STATE["device"])
        baseline.eval()
        STATE["models"]["1"] = {"model": baseline, "name": "Baseline MLP"}
        
        # Pre-load Optimized
        with open(os.path.join(base_dir, 'results', 'metrics', 'pso_best_params.json'), 'r') as f:
            best_params = json.load(f)
        optimized = FakeNewsMLP(input_dim=STATE["input_dim"], hidden_dim=best_params['hidden_dim'], dropout_rate=best_params['dropout_rate'])
        optimized.load_state_dict(torch.load(os.path.join(models_dir, 'optimized_mlp.pth'), map_location=STATE["device"]))
        optimized.to(STATE["device"])
        optimized.eval()
        STATE["models"]["2"] = {"model": optimized, "name": "PSO Optimized MLP"}
        
        print("Models and environment loaded successfully.")
    except Exception as e:
        print(f"Error loading environment during startup: {e}")

@app.post("/api/predict")
def predict(request: PredictRequest):
    if STATE["vectorizer"] is None:
        raise HTTPException(status_code=500, detail="Server environment not initialized properly.")
        
    text = request.text.strip()
    model_choice = request.model_choice
    
    if model_choice not in STATE["models"]:
        raise HTTPException(status_code=400, detail="Invalid model selection. Choose '1' or '2'.")
        
    # Validation 1: Empty input
    if not text:
        raise HTTPException(status_code=400, detail="Please enter a meaningful news article.")
        
    # Clean text
    cleaned = clean_text(text)
    
    # Validation 2: Low-information (e.g. only punctuation or stop words)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Insufficient text for reliable classification.")
        
    # Transform
    tfidf_features = STATE["vectorizer"].transform([cleaned])
    
    # Validation 3: Check if TF-IDF found any known vocabulary
    if tfidf_features.nnz == 0:
        raise HTTPException(status_code=400, detail="Insufficient text for reliable classification.")
        
    # Predict
    model_info = STATE["models"][model_choice]
    model = model_info["model"]
    device = STATE["device"]
    
    tensor_features = torch.FloatTensor(tfidf_features.toarray()).to(device)
    with torch.no_grad():
        outputs = model(tensor_features)
        probs = torch.softmax(outputs, dim=1)[0]
        pred = torch.argmax(probs).item()
        confidence = probs[pred].item()
        
    # Verified Label Mapping: 0 = FAKE, 1 = REAL (True)
    label = "FAKE" if pred == 0 else "REAL"
    
    return {
        "prediction": label,
        "confidence": confidence,
        "model": model_info["name"]
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

