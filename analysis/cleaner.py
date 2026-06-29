import re

import pandas as pd

from config import STANDARD_COLUMNS
from analysis.classifier import classify_violation


def clean_text(value):
    if pd.isna(value):
        return ""

    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
    )


def clean_penalty_amount(value):
    if pd.isna(value):
        return 0

    text = str(value)

    text = text.replace(",", "")
    text = text.replace("元", "")
    text = text.replace("新臺幣", "")
    text = text.replace("新台幣", "")
    text = text.strip()

    digits = "".join(ch for ch in text if ch.isdigit())

    if not digits:
        return 0

    return int(digits)


def clean_date(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def split_company_and_person(company_value, person_value):
    company_text = clean_text(company_value)
    person_text = clean_text(person_value)

    match = re.match(r"^(.*?)\s*[\(（](.*?)[\)）]\s*$", company_text)

    if match:
        company_name = match.group(1).strip()
        responsible_person = match.group(2).strip()
        return company_name, responsible_person

    return company_text, person_text


def clean_and_classify(df):
    if df.empty:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    df = df.copy()

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    text_columns = [
        "source_name",
        "city",
        "authority",
        "company_name",
        "responsible_person",
        "announce_date",
        "penalty_date",
        "violated_law",
        "violation_content",
        "note",
    ]

    for col in text_columns:
        df[col] = df[col].apply(clean_text)

    split_results = df.apply(
        lambda row: split_company_and_person(
            row["company_name"],
            row["responsible_person"],
        ),
        axis=1,
    )

    df["company_name"] = [item[0] for item in split_results]
    df["responsible_person"] = [item[1] for item in split_results]

    df["announce_date"] = df["announce_date"].apply(clean_date)
    df["penalty_date"] = df["penalty_date"].apply(clean_date)
    df["penalty_amount"] = df["penalty_amount"].apply(clean_penalty_amount)

    df = df[df["company_name"].astype(str).str.strip() != ""].copy()

    df["violation_category"] = df.apply(classify_violation, axis=1)

    df = df.drop_duplicates(
        subset=[
            "company_name",
            "penalty_date",
            "violated_law",
            "violation_content",
        ],
        keep="first",
    )

    return df[STANDARD_COLUMNS]