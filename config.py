import os
from pathlib import Path


# ================================
# 專案路徑設定
# ================================

BASE_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DOWNLOADED_RAW_DIR = RAW_DATA_DIR / "downloaded"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

SAMPLE_DATA_PATH = RAW_DATA_DIR / "sample_labor_violations.csv"
MOL_LOCAL_DATA_PATH = RAW_DATA_DIR / "mol_labor_violations.csv"
ANALYZED_DATA_PATH = PROCESSED_DATA_DIR / "analyzed_labor_violations.csv"


# ================================
# Render / 資料流程設定
# ================================

# Render 正式部署時建議 false，避免每次網站啟動都重新爬資料
RUN_PIPELINE_ON_STARTUP = (
    os.getenv("RUN_PIPELINE_ON_STARTUP", "false").lower() == "true"
)

# 本機需要重新整理資料時，可把這個改成 true 或設環境變數
USE_MOL_DYNAMIC_FETCH = (
    os.getenv("USE_MOL_DYNAMIC_FETCH", "true").lower() == "true"
)

USE_CACHED_MOL_FILES = True
USE_SAMPLE_FALLBACK = True


# ================================
# 勞動部縣市代碼設定
# ================================

MOL_CITY_CODES = {
    "臺北市": "63",
    "新北市": "65",
    "桃園市": "68",
    "臺中市": "66",
    "臺南市": "67",
    "高雄市": "64",
}


# ================================
# 系統標準欄位
# ================================

STANDARD_COLUMNS = [
    "source_name",
    "city",
    "authority",
    "company_name",
    "responsible_person",
    "announce_date",
    "penalty_date",
    "violated_law",
    "violation_content",
    "penalty_amount",
    "note",
    "violation_category",
]


# ================================
# 違規類型分類規則
# ================================

CATEGORY_RULES = {
    "工時問題": [
        "延長工時",
        "工時",
        "工作時間",
        "出勤紀錄",
        "休息時間",
        "超時",
        "第30條",
        "第32條",
        "第36條",
    ],
    "薪資／加班費問題": [
        "工資",
        "加班費",
        "延長工作時間工資",
        "未全額給付",
        "最低工資",
        "薪資",
        "第22條",
        "第24條",
    ],
    "休假問題": [
        "例假",
        "休息日",
        "特別休假",
        "國定假日",
        "未給假",
        "休假",
        "第38條",
        "第39條",
    ],
    "職業安全問題": [
        "職業安全",
        "職業安全衛生",
        "安全衛生",
        "職災",
        "防護",
        "危害",
        "職安",
    ],
    "勞退／保險問題": [
        "勞工退休金",
        "退休金",
        "提繳",
        "勞保",
        "就業保險",
    ],
    "職場平等問題": [
        "性別平等",
        "就業歧視",
        "育嬰留職停薪",
        "性騷擾",
        "平等",
    ],
}


# ================================
# 建立必要資料夾
# ================================

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADED_RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)