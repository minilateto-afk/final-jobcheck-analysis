import os
import shutil

from config import (
    USE_MOL_DYNAMIC_FETCH,
    USE_CACHED_MOL_FILES,
    USE_SAMPLE_FALLBACK,
    DOWNLOADED_RAW_DIR,
    SAMPLE_DATA_PATH,
    MOL_LOCAL_DATA_PATH,
)
from collectors.mol_dynamic_fetcher import download_mol_dynamic_data


def is_data_file(filename):
    lower_name = filename.lower()
    return lower_name.endswith((".csv", ".xlsx", ".xls", ".ods"))


def find_cached_mol_files():
    cached_files = []

    if not DOWNLOADED_RAW_DIR.exists():
        return cached_files

    for root, dirs, files in os.walk(DOWNLOADED_RAW_DIR):
        for filename in files:
            if "sample" in filename.lower():
                continue

            if is_data_file(filename):
                cached_files.append({
                    "source_name": "勞動部快取資料",
                    "file_path": os.path.join(root, filename),
                })

    return cached_files


def download_all_sources():
    if USE_MOL_DYNAMIC_FETCH:
        try:
            mol_files = download_mol_dynamic_data()

            if mol_files:
                print("本次已成功使用勞動部動態下載資料。", flush=True)
                return mol_files

        except Exception as error:
            print(f"勞動部動態下載失敗，改用備援資料：{error}", flush=True)

    if USE_CACHED_MOL_FILES:
        cached_files = find_cached_mol_files()

        if cached_files:
            print("本次使用上次成功下載的勞動部快取資料。", flush=True)
            return cached_files

    if MOL_LOCAL_DATA_PATH.exists():
        output_path = DOWNLOADED_RAW_DIR / "mol_labor_violations.csv"
        shutil.copyfile(MOL_LOCAL_DATA_PATH, output_path)

        return [{
            "source_name": "勞動部手動下載資料",
            "file_path": output_path,
        }]

    if USE_SAMPLE_FALLBACK and SAMPLE_DATA_PATH.exists():
        output_path = DOWNLOADED_RAW_DIR / "sample_labor_violations.csv"
        shutil.copyfile(SAMPLE_DATA_PATH, output_path)

        print("警告：目前使用內建範例資料。", flush=True)

        return [{
            "source_name": "內建範例資料",
            "file_path": output_path,
        }]

    raise FileNotFoundError("找不到可使用的資料來源。")