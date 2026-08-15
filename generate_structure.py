import os
from pathlib import Path

def create_structure(base_path: str = "."):
    base = Path(base_path)
    
    # Define directories
    directories = [
        "backend",
        "frontend",
        "data/processed",
        "data/raw",
        "models",
        "notebooks/archive",
        "results/figures/evaluation",
        "results/figures/preprocessing",
        "results/metrics",
        "scripts",
        "src/data",
        "src/evaluation",
        "src/models",
        "src/optimization",
        "src/preprocessing",
        "src/utils"
    ]
    
    # Define standalone files
    files = [
        "scripts/run_preprocessing.py",
        "scripts/run_baseline.py",
        "scripts/run_pso.py",
        "scripts/run_inference.py",
        ".gitignore",
        "README.md",
        "requirements.txt",
        "docker-compose.yml",
        "start.sh",
        "start.ps1"
    ]
    
    # Create directories
    print("Creating directories...")
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
        
    # Create __init__.py for src and its subdirectories
    print("Creating __init__.py files in src/...")
    src_path = base / "src"
    if src_path.exists():
        (src_path / "__init__.py").touch(exist_ok=True)
        for root, dirs, _ in os.walk(src_path):
            for d in dirs:
                init_file = Path(root) / d / "__init__.py"
                init_file.touch(exist_ok=True)
                
    # Create standalone files
    print("Creating placeholder files...")
    for file_path in files:
        full_path = base / file_path
        full_path.touch(exist_ok=True)
        print(f"Created file: {full_path}")

    print("Project structure generated successfully!")

if __name__ == "__main__":
    create_structure()
