import os
import re
import time
import shutil
import zipfile

import requests
import urllib3

from config import DOWNLOADED_RAW_DIR, MOL_CITY_CODES


MOL_HOME_URL = "https://announcement.mol.gov.tw/"
MOL_DOWNLOAD_URL = "https://announcement.mol.gov.tw/Download/"

# 勞動部網站的 SSL 憑證缺少 Subject Key Identifier 欄位，
# 在新版 Python / OpenSSL 下會被判定憑證驗證失敗（即使用瀏覽器開網站完全正常）。
# 這是該網站憑證設定本身的問題，這裡只針對這個政府公開資料網站關閉嚴格驗證，
# 且僅用來下載公開資料，不會傳輸任何機敏資訊。
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
VERIFY_SSL = False


def build_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://announcement.mol.gov.tw",
        "Referer": "https://announcement.mol.gov.tw/",
    }


def reset_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    os.makedirs(folder_path, exist_ok=True)


def fetch_csrf_token(session):
    response = session.get(
        MOL_HOME_URL,
        headers=build_headers(),
        timeout=30,
        verify=VERIFY_SSL,
    )

    response.raise_for_status()
    html = response.text

    patterns = [
        r'name="_csrf_token"\s+value="([^"]+)"',
        r'value="([^"]+)"\s+name="_csrf_token"',
        r'_csrf_token[^>]+value="([^"]+)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, html)

        if match:
            return match.group(1)

    raise ValueError("找不到 _csrf_token，可能是勞動部網站表單格式改變。")


def build_download_form(csrf_token, city_code):
    return {
        "_csrf_token": (None, csrf_token),
        "CITYNO": (None, city_code),
        "UNITNAME": (None, ""),
        "DOCstartDate": (None, ""),
        "DOCEndDate": (None, ""),
        "REGNUMBER": (None, ""),
        "REGNO": (None, ""),
        "downloadType": (None, "3"),
        "sortName3": (None, ""),
        "sortName1": (None, ""),
        "sortName2": (None, ""),
        "Page3": (None, "1"),
        "Page1": (None, "1"),
        "Page2": (None, "1"),
    }


def extract_zip_files(zip_path, extract_dir):
    reset_folder(extract_dir)

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(extract_dir)

    data_files = []

    for root, dirs, files in os.walk(extract_dir):
        for filename in files:
            lower_name = filename.lower()

            if lower_name.endswith((".csv", ".xlsx", ".xls", ".ods")):
                data_files.append(os.path.join(root, filename))

    if not data_files:
        raise FileNotFoundError("zip 解壓縮後找不到 CSV / Excel / ODS 檔案。")

    return data_files


def download_single_city(city_name, city_code):
    session = requests.Session()
    csrf_token = fetch_csrf_token(session)
    form_data = build_download_form(csrf_token, city_code)

    response = session.post(
        MOL_DOWNLOAD_URL,
        headers=build_headers(),
        files=form_data,
        timeout=120,
        verify=VERIFY_SSL,
    )

    response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    if "zip" not in content_type.lower():
        raise ValueError(
            f"{city_name} 回傳不是 zip，content-type={content_type}。"
        )

    zip_path = DOWNLOADED_RAW_DIR / f"mol_{city_name}.zip"

    with open(zip_path, "wb") as file:
        file.write(response.content)

    extract_dir = DOWNLOADED_RAW_DIR / f"mol_{city_name}"
    data_file_paths = extract_zip_files(zip_path, extract_dir)

    results = []

    for file_path in data_file_paths:
        results.append({
            "source_name": f"勞動部動態下載資料－{city_name}",
            "file_path": file_path,
        })

    return results


def download_mol_dynamic_data():
    downloaded_files = []

    for city_name, city_code in MOL_CITY_CODES.items():
        try:
            city_results = download_single_city(city_name, city_code)
            downloaded_files.extend(city_results)

            print(f"成功下載勞動部資料：{city_name}", flush=True)

            time.sleep(0.8)

        except Exception as error:
            print(f"下載勞動部資料失敗：{city_name}，錯誤：{error}", flush=True)

    if not downloaded_files:
        raise RuntimeError("勞動部動態下載全部失敗。")

    return downloaded_files