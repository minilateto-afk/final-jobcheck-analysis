from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from analysis.analyzer import run_data_pipeline


if __name__ == "__main__":
    run_data_pipeline()