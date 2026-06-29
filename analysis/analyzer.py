import os
import re
import traceback

import pandas as pd

from config import (
    ANALYZED_DATA_PATH,
    SAMPLE_DATA_PATH,
    STANDARD_COLUMNS,
)
from collectors.gov_open_data_fetcher import download_all_sources
from analysis.data_loader import read_data_file
from analysis.normalizer import normalize_columns
from analysis.cleaner import clean_and_classify


def run_data_pipeline():
    print("開始執行資料流程...", flush=True)

    source_files = download_all_sources()
    normalized_list = []

    for source in source_files:
        source_name = source.get("source_name", "未知資料來源")
        file_path = source.get("file_path", "")

        try:
            print(f"讀取資料來源：{source_name}，路徑：{file_path}", flush=True)

            raw_df = read_data_file(file_path)
            normalized_df = normalize_columns(raw_df, source_name)
            normalized_list.append(normalized_df)

        except Exception as error:
            print(f"讀取或標準化資料失敗：{source_name}，錯誤：{error}", flush=True)

    if not normalized_list:
        print("沒有任何官方資料成功讀取，改用範例資料。", flush=True)

        raw_df = read_data_file(SAMPLE_DATA_PATH)
        normalized_df = normalize_columns(raw_df, "內建範例資料")
        normalized_list.append(normalized_df)

    combined_df = pd.concat(normalized_list, ignore_index=True)
    final_df = clean_and_classify(combined_df)

    final_df.to_csv(ANALYZED_DATA_PATH, index=False, encoding="utf-8-sig")

    try:
        from analysis.database import replace_database_records
        replace_database_records(final_df)
    except Exception as error:
        print(f"同步 PostgreSQL 失敗：{error}", flush=True)

    print(f"資料流程完成，共 {len(final_df)} 筆資料。", flush=True)

    return final_df


def load_analyzed_data():
    from analysis.database import load_records_from_database_or_csv

    df = load_records_from_database_or_csv()

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["penalty_amount"] = (
        pd.to_numeric(df["penalty_amount"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    return df[STANDARD_COLUMNS]


def startup_prepare_data():
    try:
        return run_data_pipeline()

    except Exception as error:
        print("啟動時資料流程失敗，改用既有資料或範例資料。", flush=True)
        print(f"錯誤：{error}", flush=True)
        traceback.print_exc()

        existing_df = load_analyzed_data()

        if not existing_df.empty:
            return existing_df

        raw_df = read_data_file(SAMPLE_DATA_PATH)
        normalized_df = normalize_columns(raw_df, "內建範例資料")
        final_df = clean_and_classify(normalized_df)
        final_df.to_csv(ANALYZED_DATA_PATH, index=False, encoding="utf-8-sig")

        return final_df


def series_to_items(series):
    if series is None or series.empty:
        return []

    max_value = int(series.max()) if int(series.max()) > 0 else 1
    items = []

    for name, value in series.items():
        value = int(value)
        percent = round((value / max_value) * 100, 2)

        items.append({
            "name": str(name) if str(name).strip() else "未標示",
            "value": value,
            "percent": percent,
        })

    return items


def extract_year(value):
    text = str(value).strip()

    if not text:
        return "未標示"

    match = re.search(r"(\d{2,4})", text)

    if not match:
        return "未標示"

    year = match.group(1)

    if len(year) == 3:
        return f"民國 {year} 年"

    if len(year) == 4:
        return f"{year} 年"

    return "未標示"


def get_summary_cards(df):
    if df.empty:
        return {
            "total_records": 0,
            "total_companies": 0,
            "total_cities": 0,
            "repeated_companies": 0,
            "total_penalty": 0,
            "top_category": "無資料",
            "latest_date": "無資料",
        }

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    company_count = int(
        df["company_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    city_count = int(
        df["city"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    company_counts = (
        df["company_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
    )

    repeated_companies = int((company_counts >= 2).sum())

    category_counts = (
        df["violation_category"]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
    )

    top_category = category_counts.index[0] if not category_counts.empty else "無資料"

    dates = df["announce_date"].dropna().astype(str).str.strip()
    dates = dates[dates != ""]
    latest_date = str(dates.max()) if not dates.empty else "無資料"

    total_penalty = int(
        pd.to_numeric(df["penalty_amount"], errors="coerce")
        .fillna(0)
        .sum()
    )

    return {
        "total_records": int(len(df)),
        "total_companies": company_count,
        "total_cities": city_count,
        "repeated_companies": repeated_companies,
        "total_penalty": total_penalty,
        "top_category": top_category,
        "latest_date": latest_date,
    }


def get_dashboard_data(df):
    if df.empty:
        return {
            "summary": get_summary_cards(df),
            "category_items": [],
            "city_items": [],
            "top_company_items": [],
            "source_items": [],
            "year_items": [],
        }

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    year_series = df["announce_date"].apply(extract_year)

    return {
        "summary": get_summary_cards(df),
        "category_items": series_to_items(
            df["violation_category"].fillna("未分類").replace("", "未分類").value_counts().head(10)
        ),
        "city_items": series_to_items(
            df["city"].fillna("未標示").replace("", "未標示").value_counts().head(10)
        ),
        "top_company_items": series_to_items(
            df["company_name"].fillna("未標示").replace("", "未標示").value_counts().head(10)
        ),
        "source_items": series_to_items(
            df["source_name"].fillna("未標示").replace("", "未標示").value_counts().head(10)
        ),
        "year_items": series_to_items(
            year_series.value_counts().head(10)
        ),
    }