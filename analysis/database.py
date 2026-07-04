import os
from datetime import datetime, timezone

import pandas as pd
import psycopg2
import psycopg2.extras

from config import ANALYZED_DATA_PATH, STANDARD_COLUMNS


TABLE_NAME = "violation_records"
META_TABLE_NAME = "pipeline_meta"


# ================================
# 這裡是本專案實際使用的 SQL 語法
# 全部用 psycopg2 直接下指令，不透過任何 ORM 包裝
# ================================

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    source_name TEXT,
    city TEXT,
    authority TEXT,
    company_name TEXT,
    responsible_person TEXT,
    announce_date TEXT,
    penalty_date TEXT,
    violated_law TEXT,
    violation_content TEXT,
    penalty_amount INTEGER,
    note TEXT,
    violation_category TEXT
);
"""

CREATE_META_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {META_TABLE_NAME} (
    id INTEGER PRIMARY KEY,
    last_updated TIMESTAMP,
    source TEXT
);
"""

TRUNCATE_TABLE_SQL = f"TRUNCATE TABLE {TABLE_NAME} RESTART IDENTITY;"

INSERT_SQL = f"""
INSERT INTO {TABLE_NAME} (
    source_name, city, authority, company_name, responsible_person,
    announce_date, penalty_date, violated_law, violation_content,
    penalty_amount, note, violation_category
) VALUES %s
"""

SELECT_ALL_SQL = f"SELECT {', '.join(STANDARD_COLUMNS)} FROM {TABLE_NAME};"

COUNT_SQL = f"SELECT COUNT(*) FROM {TABLE_NAME};"

UPSERT_META_SQL = f"""
INSERT INTO {META_TABLE_NAME} (id, last_updated, source)
VALUES (1, %s, %s)
ON CONFLICT (id) DO UPDATE
SET last_updated = EXCLUDED.last_updated,
    source = EXCLUDED.source;
"""

SELECT_META_SQL = f"SELECT last_updated, source FROM {META_TABLE_NAME} WHERE id = 1;"


def get_database_url():
    return os.getenv("DATABASE_URL", "").strip()


def get_connection():
    """
    用 psycopg2 直接建立 PostgreSQL 連線。
    沒有設定 DATABASE_URL 就回傳 None，讓外層改用 CSV 模式（本機開發用）。
    """
    database_url = get_database_url()

    if not database_url:
        return None

    return psycopg2.connect(database_url)


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


def table_has_data(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s);", (f"public.{TABLE_NAME}",))
        table_exists = cur.fetchone()[0]

        if not table_exists:
            return False

        cur.execute(COUNT_SQL)
        count = cur.fetchone()[0]

        return bool(count and count > 0)


def _write_meta(conn, source):
    with conn.cursor() as cur:
        cur.execute(CREATE_META_TABLE_SQL)
        cur.execute(UPSERT_META_SQL, (datetime.now(timezone.utc), source))

    conn.commit()


def get_last_updated_info():
    """給 /about 頁面顯示資料庫最後一次由爬蟲寫入的時間。"""
    conn = get_connection()

    if conn is None:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_META_TABLE_SQL)
            cur.execute(SELECT_META_SQL)
            row = cur.fetchone()
        conn.commit()

        if row is None:
            return None

        return {"last_updated": row[0], "source": row[1]}

    except Exception:
        return None

    finally:
        conn.close()


def seed_database_if_empty():
    """
    容器 / 服務啟動時呼叫。
    先用 SQL 建表，如果表是空的，代表這是全新的資料庫，
    直接觸發爬蟲流程 run_data_pipeline()，
    確保資料庫的資料一定是「爬蟲 -> 清理 -> SQL 寫入」出來的，
    不是手動塞進去的。
    """
    conn = get_connection()

    if conn is None:
        print("未設定 DATABASE_URL，目前使用 CSV 模式。", flush=True)
        return

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()

        if table_has_data(conn):
            print("PostgreSQL 已有資料，不重複執行爬蟲。", flush=True)
            return

    finally:
        conn.close()

    print("PostgreSQL 目前是空的，開始執行爬蟲流程建立初始資料...", flush=True)

    # 延遲 import，避免 analyzer <-> database 互相 import 造成循環引用
    from analysis.analyzer import run_data_pipeline

    run_data_pipeline()


def replace_database_records(df, source="scrape"):
    """
    用 psycopg2 執行 TRUNCATE + INSERT INTO，
    把清理後的資料整批寫進 PostgreSQL。
    """
    conn = get_connection()

    if conn is None:
        return

    df = normalize_dataframe(df)

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(TRUNCATE_TABLE_SQL)

            rows = [
                tuple(row)
                for row in df[STANDARD_COLUMNS].itertuples(index=False, name=None)
            ]

            psycopg2.extras.execute_values(cur, INSERT_SQL, rows, page_size=1000)

        conn.commit()
        _write_meta(conn, source=source)

        print(f"已用 SQL (INSERT INTO) 寫入 PostgreSQL，共 {len(df)} 筆資料。", flush=True)

    finally:
        conn.close()


def load_records_from_database_or_csv():
    """
    用 psycopg2 執行 SELECT，把資料庫內容讀回 DataFrame。
    如果沒有資料庫連線或查詢失敗，才退回讀本機 CSV（開發/展示用的備援）。
    """
    conn = get_connection()

    if conn is not None:
        try:
            with conn.cursor() as cur:
                cur.execute(SELECT_ALL_SQL)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

            df = pd.DataFrame(rows, columns=columns)
            return normalize_dataframe(df)

        except Exception as error:
            print(f"讀取 PostgreSQL 失敗，改用 CSV：{error}", flush=True)

        finally:
            conn.close()

    if ANALYZED_DATA_PATH.exists():
        df = pd.read_csv(ANALYZED_DATA_PATH, encoding="utf-8-sig")
        return normalize_dataframe(df)

    return pd.DataFrame(columns=STANDARD_COLUMNS)