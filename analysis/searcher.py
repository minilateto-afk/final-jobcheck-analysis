import pandas as pd

from config import STANDARD_COLUMNS


def get_observation_info(record_count):
    if record_count <= 0:
        return {
            "label": "查無紀錄",
            "class_name": "label-blue",
            "description": "目前匯入資料中未查到相關公開紀錄。",
        }

    if record_count == 1:
        return {
            "label": "單筆紀錄",
            "class_name": "label-green",
            "description": "查到少量公開紀錄，建議閱讀違反法規與公告日期。",
        }

    if record_count <= 4:
        return {
            "label": "多筆紀錄",
            "class_name": "label-yellow",
            "description": "同一事業單位出現多筆公開紀錄，建議比對日期與類型。",
        }

    return {
        "label": "重複出現",
        "class_name": "label-orange",
        "description": "同一事業單位多次出現在公開資料中，求職前可特別留意紀錄內容。",
    }


def attach_observation_labels(result_df, full_df):
    if result_df.empty:
        return result_df

    result_df = result_df.copy()

    company_counts = (
        full_df["company_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .to_dict()
    )

    result_df["company_record_count"] = (
        result_df["company_name"]
        .astype(str)
        .str.strip()
        .map(company_counts)
        .fillna(0)
        .astype(int)
    )

    result_df["observation_label"] = result_df["company_record_count"].apply(
        lambda count: get_observation_info(count)["label"]
    )

    result_df["observation_class"] = result_df["company_record_count"].apply(
        lambda count: get_observation_info(count)["class_name"]
    )

    return result_df


def sort_records(result_df):
    if result_df.empty:
        return result_df

    result_df = result_df.copy()

    if "announce_date" in result_df.columns:
        result_df = result_df.sort_values(
            by="announce_date",
            ascending=False,
        )

    return result_df


def filter_records(df, keyword="", city="", category=""):
    if df.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    df = df.copy()

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    result_df = df

    keyword = str(keyword).strip()
    city = str(city).strip()
    category = str(category).strip()

    if keyword:
        keyword_mask = (
            result_df["company_name"]
            .astype(str)
            .str.contains(keyword, case=False, na=False, regex=False)
        )

        result_df = result_df[keyword_mask]

    if city:
        result_df = result_df[
            result_df["city"].astype(str).str.strip() == city
        ]

    if category:
        result_df = result_df[
            result_df["violation_category"].astype(str).str.strip() == category
        ]

    result_df = attach_observation_labels(result_df, df)
    result_df = sort_records(result_df)

    return result_df


def get_company_summary(result_df, keyword):
    if result_df.empty:
        observation = get_observation_info(0)

        return {
            "keyword": keyword,
            "found": False,
            "total_records": 0,
            "categories": [],
            "latest_date": "無資料",
            "total_penalty": 0,
            "main_category": "無資料",
            "observation_label": observation["label"],
            "observation_class": observation["class_name"],
            "observation_description": observation["description"],
        }

    categories = (
        result_df["violation_category"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    category_counts = categories.value_counts()
    category_list = category_counts.index.tolist()

    dates = result_df["announce_date"].dropna().astype(str).str.strip()
    dates = dates[dates != ""]
    latest_date = str(dates.max()) if not dates.empty else "無資料"

    total_penalty = int(
        pd.to_numeric(result_df["penalty_amount"], errors="coerce")
        .fillna(0)
        .sum()
    )

    observation = get_observation_info(len(result_df))

    return {
        "keyword": keyword,
        "found": True,
        "total_records": int(len(result_df)),
        "categories": category_list,
        "latest_date": latest_date,
        "total_penalty": total_penalty,
        "main_category": category_list[0] if category_list else "無資料",
        "observation_label": observation["label"],
        "observation_class": observation["class_name"],
        "observation_description": observation["description"],
    }