# JobCheck：公開違反勞動法令資料查詢與求職參考分析系統

JobCheck 是一個以公開違反勞動法令資料為基礎的 Flask 專題網站。系統透過資料下載、欄位標準化、資料清理、違規類型分類、PostgreSQL 儲存與視覺化分析，協助求職者在投遞履歷或面試前，多一項公開紀錄參考。

## 專題定位

本專題不是公司黑名單，也不直接評斷企業好壞，而是將政府公開資料整理成較容易查詢與理解的求職參考工具。

## 使用技術

- Python
- Flask
- pandas
- PostgreSQL（透過 psycopg2 直接下 SQL，未使用 ORM）
- requests（爬蟲核心：`collectors/mol_dynamic_fetcher.py`）
- Render（Web Service + PostgreSQL，設定於 `render.yaml`）
- GitHub

## 主要功能

1. 公司名稱查詢
2. 公開違反勞動法令紀錄列表
3. 違規類型分類
4. 縣市與資料來源統計
5. 重複出現事業單位統計
6. Render PostgreSQL 部署
7. 資料處理流程說明

## 資料流程

勞動部公開查詢系統 (collectors/mol_dynamic_fetcher.py)
→ 欄位標準化 (analysis/normalizer.py)
→ 清理與分類 (analysis/cleaner.py, analysis/classifier.py)
→ 存成 CSV + 寫入 PostgreSQL (analysis/database.py)
→ Flask 網站讀取顯示 (app.py)

## 本機執行

```bash
pip install -r requirements.txt
python scripts/init_db.py
python app.py
```

## Render 部署

專案根目錄已附上 `render.yaml`，在 Render 上選擇「New Blueprint」並指向這個 GitHub repo，即可自動建立 Web Service 與 PostgreSQL，並自動注入 `DATABASE_URL`。第一次啟動時，`app.py` 會偵測資料庫是否為空，若為空則自動觸發爬蟲流程寫入資料。

## 系統限制

- 目前爬蟲僅涵蓋六都（臺北、新北、桃園、臺中、臺南、高雄），可視需求擴充 `config.py` 的 `MOL_CITY_CODES`。
- 查無紀錄不代表公司完全沒有勞動爭議，僅代表目前匯入資料中未查到符合條件的公開紀錄。