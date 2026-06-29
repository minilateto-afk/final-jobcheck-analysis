from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from analysis.database import seed_database_if_empty


if __name__ == "__main__":
    seed_database_if_empty()