"""
scripts/crawler.py

這支程式就是本專題的「爬蟲程式」進入點，跟資料庫、清理邏輯完全分開，
方便單獨執行、單獨檢查。

執行後會依序做：
1. 連線勞動部「違反勞動法令事業單位查詢系統」：
   https://announcement.mol.gov.tw/
2. 依縣市代碼送出下載表單，取得公開裁罰資料（zip，內含 CSV/Excel）
3. 把下載到、尚未清理的原始資料合併，另存成一份 CSV：
   data/raw/downloaded/mol_raw_scraped.csv

這份 CSV 就是「爬蟲直接從網站取得的資料」，可以打開來看內容，
和資料庫、SQL 完全無關，是清理/寫入資料庫流程的前一步。

執行方式：
    python scripts/crawler.py
"""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from config import DOWNLOADED_RAW_DIR
from collectors.mol_dynamic_fetcher import MOL_HOME_URL, download_mol_dynamic_data
from analysis.data_loader import read_data_file


RAW_CSV_OUTPUT_PATH = DOWNLOADED_RAW_DIR / "mol_raw_scraped.csv"


def crawl_and_save_csv():
    print(f"目標網站：{MOL_HOME_URL}", flush=True)
    print("開始爬取勞動部公開違反勞動法令事業單位資料...", flush=True)

    downloaded_files = download_mol_dynamic_data()

    raw_frames = []

    for item in downloaded_files:
        file_path = item["file_path"]
        source_name = item["source_name"]

        try:
            df = read_data_file(file_path)
            df["__source_name"] = source_name
            raw_frames.append(df)
        except Exception as error:
            print(f"讀取 {file_path} 失敗：{error}", flush=True)

    if not raw_frames:
        raise RuntimeError("爬蟲沒有取得任何資料，無法存成 CSV。")

    combined_df = pd.concat(raw_frames, ignore_index=True)
    combined_df.to_csv(RAW_CSV_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"爬蟲完成，共取得 {len(combined_df)} 筆原始資料。", flush=True)
    print(f"已將爬蟲資料存成 CSV：{RAW_CSV_OUTPUT_PATH}", flush=True)

    return RAW_CSV_OUTPUT_PATH


if __name__ == "__main__":
    crawl_and_save_csv()