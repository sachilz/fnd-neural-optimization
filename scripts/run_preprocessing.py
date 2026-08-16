import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.seed import set_seed
set_seed(42)
from preprocessing.pipeline import preprocess_pipeline

def main():
    fake_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'Fake.csv'))
    true_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'True.csv'))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'processed'))

    print(f"Running preprocessing pipeline...")
    print(f"Input: {fake_path}, {true_path}")
    print(f"Output: {output_dir}")

    metadata = preprocess_pipeline(
        fake_path=fake_path,
        true_path=true_path,
        output_dir=output_dir,
        max_features=5000,
        random_state=42
    )
    
    print("\nPreprocessing complete!")
    print(f"Empty text removed: {metadata['empty_text_removed']}")
    print(f"Exact duplicates removed: {metadata['exact_duplicate_count']}")
    print(f"Final Fake rows: {metadata['final_fake_rows']}")
    print(f"Final True rows: {metadata['final_true_rows']}")
    print(f"\nMetadata saved in: {output_dir}/preprocessing_metadata.json")

if __name__ == '__main__':
    main()
