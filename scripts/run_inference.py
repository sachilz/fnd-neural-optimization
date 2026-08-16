import os
import sys
import json
import torch
import joblib
import numpy as np

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from preprocessing.clean import clean_text
from models.baseline import FakeNewsMLP

def load_environment():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(base_dir, 'data', 'processed')
    models_dir = os.path.join(base_dir, 'models')
    
    # Load metadata
    with open(os.path.join(data_dir, 'preprocessing_metadata.json'), 'r') as f:
        meta = json.load(f)
    input_dim = meta['max_features']
    
    # Load vectorizer
    vectorizer = joblib.load(os.path.join(data_dir, 'tfidf_vectorizer.pkl'))
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    return base_dir, models_dir, input_dim, vectorizer, device

def load_model(model_choice, base_dir, models_dir, input_dim, device):
    if model_choice == '1':
        # Baseline
        model = FakeNewsMLP(input_dim=input_dim, hidden_dim=128, dropout_rate=0.5)
        model.load_state_dict(torch.load(os.path.join(models_dir, 'baseline_mlp.pth'), map_location=device))
        model_name = "Baseline MLP"
    else:
        # PSO Optimized
        with open(os.path.join(base_dir, 'results', 'metrics', 'pso_best_params.json'), 'r') as f:
            best_params = json.load(f)
        model = FakeNewsMLP(input_dim=input_dim, hidden_dim=best_params['hidden_dim'], dropout_rate=best_params['dropout_rate'])
        model.load_state_dict(torch.load(os.path.join(models_dir, 'optimized_mlp.pth'), map_location=device))
        model_name = "PSO Optimized MLP"
        
    model.to(device)
    model.eval()
    return model, model_name

def main():
    print("========================================")
    print("        FAKE NEWS DETECTOR              ")
    print("========================================")
    
    try:
        base_dir, models_dir, input_dim, vectorizer, device = load_environment()
    except Exception as e:
        print(f"Error loading required files: {e}")
        return

    print("\nChoose model:")
    print("1. Baseline MLP")
    print("2. PSO Optimized MLP")
    
    while True:
        choice = input("\nSelect [1/2]: ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please select 1 or 2.")
        
    model, model_name = load_model(choice, base_dir, models_dir, input_dim, device)
    print(f"\nLoaded {model_name} successfully.\n")
    
    try:
        while True:
            text = input("Enter news article:\n> ").strip()
            
            # Validation 1: Empty input
            if not text:
                print("Please enter a meaningful news article.\n")
                continue
                
            # Clean text
            cleaned = clean_text(text)
            
            # Validation 2: Low-information (e.g. only punctuation or stop words)
            if not cleaned:
                print("Please enter a meaningful news article.\n")
                continue
                
            # Transform
            tfidf_features = vectorizer.transform([cleaned])
            
            # Validation 3: Check if TF-IDF found any known vocabulary
            if tfidf_features.nnz == 0:
                print("Please enter a meaningful news article.\n")
                continue
                
            # Predict
            tensor_features = torch.FloatTensor(tfidf_features.toarray()).to(device)
            with torch.no_grad():
                outputs = model(tensor_features)
                probs = torch.softmax(outputs, dim=1)[0]
                pred = torch.argmax(probs).item()
                confidence = probs[pred].item()
                
            # Verified Label Mapping: 0 = FAKE, 1 = REAL (True)
            label = "FAKE" if pred == 0 else "REAL"
            
            print("\n----------------------------------------")
            print(f"Prediction: {label}")
            print(f"Confidence: {confidence * 100:.2f}%")
            print("----------------------------------------\n")
            
            again = input("Enter another article? [Y/n]: ").strip().lower()
            if again == 'n':
                print("\nGoodbye! 👋")
                break
    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye! 👋")
        sys.exit(0)

if __name__ == '__main__':
    main()
