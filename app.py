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




if RUN_PIPELINE_ON_STARTUP:
    startup_prepare_data()
else:
    seed_database_if_empty()