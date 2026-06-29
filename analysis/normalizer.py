import pandas as pd

from config import STANDARD_COLUMNS


def find_column(df_columns, candidates):
    for candidate in candidates:
        for col in df_columns:
            if candidate == col:
                return col

    for candidate in candidates:
        for col in df_columns:
            if candidate in col:
                return col

    return None


def normalize_columns(df, source_name):
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    normalized_df = pd.DataFrame()

    column_candidates = {
        "city": [
            "縣市／單位別",
            "縣市/單位別",
            "縣市",
            "縣市別",
            "地方主管機關",
            "主管機關",
            "單位別",
        ],
        "authority": [
            "縣市／單位別",
            "縣市/單位別",
            "主管機關",
            "處分機關",
            "單位別",
        ],
        "company_name": [
            "事業單位名稱",
            "事業單位",
            "公司名稱",
            "單位名稱",
            "雇主名稱",
            "受處分事業單位",
            "自然人姓名",
        ],
        "responsible_person": [
            "負責人",
            "代表人",
            "事業主",
            "事業單位名稱(負責人)",
            "自然人姓名",
        ],
        "announce_date": [
            "公告日期",
            "公布日期",
            "公告年月日",
        ],
        "penalty_date": [
            "處分日期",
            "裁處日期",
            "處分年月日",
        ],
        "violated_law": [
            "違反法規條款",
            "違反法規法條",
            "違法法規法條",
            "違反法令",
            "違反條文",
            "法規法條",
            "違反法規",
        ],
        "violation_content": [
            "法條敘述",
            "違反法規內容",
            "違法事實",
            "違規內容",
            "違反內容",
            "違法內容",
        ],
        "penalty_amount": [
            "處分金額／滯納金",
            "罰鍰金額",
            "處分金額",
            "罰鍰",
            "罰鍰金額或滯納金",
            "罰鍰金額(元)",
        ],
        "note": [
            "備註",
            "備註說明",
            "說明",
            "其他",
        ],
    }

    normalized_df["source_name"] = [source_name] * len(df)

    for standard_col, candidates in column_candidates.items():
        matched_col = find_column(df.columns, candidates)

        if matched_col:
            normalized_df[standard_col] = df[matched_col]
        else:
            normalized_df[standard_col] = ""

    for col in STANDARD_COLUMNS:
        if col not in normalized_df.columns:
            normalized_df[col] = ""

    return normalized_df[STANDARD_COLUMNS]