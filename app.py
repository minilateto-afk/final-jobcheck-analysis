import os

from flask import Flask, render_template, request

from config import ANALYZED_DATA_PATH, RUN_PIPELINE_ON_STARTUP
from analysis.analyzer import (
    startup_prepare_data,
    load_analyzed_data,
    get_summary_cards,
    get_dashboard_data,
)
from analysis.database import seed_database_if_empty
from analysis.searcher import (
    filter_records,
    get_company_summary,
    attach_observation_labels,
)


app = Flask(__name__)


# ================================
# Jinja Filter
# ================================

@app.template_filter("money")
def format_money(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return "0"


# ================================
# 啟動資料流程
# ================================
# RUN_PIPELINE_ON_STARTUP=true：每次啟動都強制重新爬蟲（本機測試用）
# RUN_PIPELINE_ON_STARTUP=false（Render 正式環境預設）：
#   只在 PostgreSQL 是空的情況下才自動觸發爬蟲，
#   確保 Render 第一次部署時資料庫一定會被建表 + 塞入資料，
#   不需要手動連進 shell 跑 init_db.py。

if RUN_PIPELINE_ON_STARTUP:
    startup_prepare_data()
else:
    seed_database_if_empty()


# ================================
# Routes
# ================================

@app.route("/")
def index():
    df = load_analyzed_data()
    summary = get_summary_cards(df)
    dashboard_data = get_dashboard_data(df)

    return render_template(
        "index.html",
        summary=summary,
        category_items=dashboard_data["category_items"],
        city_items=dashboard_data["city_items"],
        top_company_items=dashboard_data["top_company_items"],
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    keyword = request.values.get("keyword", "").strip()

    df = load_analyzed_data()
    result_df = filter_records(df, keyword=keyword)
    company_summary = get_company_summary(result_df, keyword)

    records = result_df.head(120).to_dict(orient="records")

    return render_template(
        "search.html",
        keyword=keyword,
        records=records,
        company_summary=company_summary,
    )


@app.route("/dashboard")
def dashboard():
    df = load_analyzed_data()
    dashboard_data = get_dashboard_data(df)

    return render_template(
        "dashboard.html",
        summary=dashboard_data["summary"],
        category_items=dashboard_data["category_items"],
        city_items=dashboard_data["city_items"],
        top_company_items=dashboard_data["top_company_items"],
        source_items=dashboard_data["source_items"],
        year_items=dashboard_data["year_items"],
    )


@app.route("/records")
def records():
    keyword = request.args.get("keyword", "").strip()
    city = request.args.get("city", "").strip()
    category = request.args.get("category", "").strip()

    df = load_analyzed_data()

    filtered_df = filter_records(
        df,
        keyword=keyword,
        city=city,
        category=category,
    )

    labeled_df = attach_observation_labels(filtered_df, df)

    cities = sorted(
        [item for item in df["city"].dropna().astype(str).unique() if item.strip()]
    )
    categories = sorted(
        [item for item in df["violation_category"].dropna().astype(str).unique() if item.strip()]
    )

    return render_template(
        "records.html",
        records=labeled_df.head(200).to_dict(orient="records"),
        keyword=keyword,
        city=city,
        category=category,
        cities=cities,
        categories=categories,
        total_count=len(filtered_df),
    )


@app.route("/about")
def about():
    df = load_analyzed_data()
    summary = get_summary_cards(df)

    return render_template(
        "about.html",
        summary=summary,
        data_path=str(ANALYZED_DATA_PATH),
    )


@app.route("/health")
def health():
    df = load_analyzed_data()

    return {
        "status": "ok",
        "records": int(len(df)),
        "companies": int(df["company_name"].nunique()) if not df.empty else 0,
        "data_path": str(ANALYZED_DATA_PATH),
        "database_mode": bool(os.getenv("DATABASE_URL")),
    }


# ================================
# 本機啟動
# ================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )