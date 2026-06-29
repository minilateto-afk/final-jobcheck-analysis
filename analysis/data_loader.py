import csv

import pandas as pd


def looks_like_header(row):
    keywords = [
        "縣市",
        "單位",
        "公告日期",
        "處分日期",
        "事業單位",
        "名稱",
        "違反",
        "法規",
        "法條",
        "罰鍰",
        "備註",
    ]

    joined = " ".join(str(cell).strip() for cell in row)
    hit_count = sum(1 for keyword in keywords if keyword in joined)

    return hit_count >= 3


def read_messy_csv(file_path, encoding):
    with open(file_path, "r", encoding=encoding, errors="replace", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    if not rows:
        return pd.DataFrame()

    header_index = 0

    for index, row in enumerate(rows[:20]):
        if looks_like_header(row):
            header_index = index
            break

    header = [str(col).strip() for col in rows[header_index]]

    fixed_header = []
    seen = {}

    for index, col in enumerate(header):
        if not col:
            col = f"未命名欄位{index + 1}"

        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 1

        fixed_header.append(col)

    header = fixed_header
    header_len = len(header)

    fixed_rows = []

    for row in rows[header_index + 1:]:
        if not row or all(str(cell).strip() == "" for cell in row):
            continue

        if len(row) > header_len:
            row = row[:header_len - 1] + [",".join(row[header_len - 1:])]

        if len(row) < header_len:
            row = row + [""] * (header_len - len(row))

        fixed_rows.append(row)

    df = pd.DataFrame(fixed_rows, columns=header)

    print(f"成功讀取 CSV：{file_path}", flush=True)
    print(f"偵測表頭：{list(df.columns)}", flush=True)
    print(f"原始資料筆數：{len(df)}", flush=True)

    return df


def read_data_file(file_path):
    file_path = str(file_path)
    lower_path = file_path.lower()

    if lower_path.endswith(".csv"):
        last_error = None

        for encoding in ["utf-8-sig", "utf-8", "cp950", "big5"]:
            try:
                return read_messy_csv(file_path, encoding)
            except Exception as error:
                last_error = error

        raise last_error

    if lower_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)

    if lower_path.endswith(".ods"):
        return pd.read_excel(file_path, engine="odf")

    raise ValueError(f"不支援的資料格式：{file_path}")