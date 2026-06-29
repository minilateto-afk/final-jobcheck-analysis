import os

import pandas as pd
from sqlalchemy import create_engine, text

from config import ANALYZED_DATA_PATH, STANDARD_COLUMNS


TABLE_NAME = "violation_records"


def get_database_url():
    database_url = os.getenv("DATABASE_URL", "").strip()

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1,
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1,
        )

    return database_url


def get_engine():
    database_url = get_database_url()

    if not database_url:
        return None

    return create_engine(database_url, pool_pre_ping=True)


def normalize_dataframe(df):
    df = df.copy()

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[STANDARD_COLUMNS]

    df["penalty_amount"] = (
        pd.to_numeric(df["penalty_amount"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    for col in STANDARD_COLUMNS:
        if col != "penalty_amount":
            df[col] = df[col].fillna("").astype(str)

    return df


def table_has_data(engine):
    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT to_regclass('public.violation_records')")
        ).scalar()

        if not table_exists:
            return False

        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        ).scalar()

        return bool(count and count > 0)


def seed_database_if_empty():
    engine = get_engine()

    if engine is None:
        print("未設定 DATABASE_URL，目前使用 CSV 模式。", flush=True)
        return

    if table_has_data(engine):
        print("PostgreSQL 已有資料，不重複匯入。", flush=True)
        return

    if not ANALYZED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"找不到初始資料檔：{ANALYZED_DATA_PATH}"
        )

    df = pd.read_csv(ANALYZED_DATA_PATH, encoding="utf-8-sig")
    df = normalize_dataframe(df)

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )

    print(f"已匯入 PostgreSQL，共 {len(df)} 筆資料。", flush=True)


def replace_database_records(df):
    engine = get_engine()

    if engine is None:
        return

    df = normalize_dataframe(df)

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        method="multi",
    )

    print(f"已更新 PostgreSQL，共 {len(df)} 筆資料。", flush=True)


def load_records_from_database_or_csv():
    engine = get_engine()

    if engine is not None:
        try:
            df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
            return normalize_dataframe(df)
        except Exception as error:
            print(f"讀取 PostgreSQL 失敗，改用 CSV：{error}", flush=True)

    if ANALYZED_DATA_PATH.exists():
        df = pd.read_csv(ANALYZED_DATA_PATH, encoding="utf-8-sig")
        return normalize_dataframe(df)

    return pd.DataFrame(columns=STANDARD_COLUMNS)