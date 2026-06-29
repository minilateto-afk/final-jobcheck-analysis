# JobCheck：公開違反勞動法令資料查詢與求職參考分析系統

JobCheck 是一個以公開違反勞動法令資料為基礎的 Flask 專題網站。系統透過資料下載、欄位標準化、資料清理、違規類型分類、PostgreSQL 儲存與視覺化分析，協助求職者在投遞履歷或面試前，多一項公開紀錄參考。

## 專題定位

本專題不是公司黑名單，也不直接評斷企業好壞，而是將政府公開資料整理成較容易查詢與理解的求職參考工具。

## 使用技術

- Python
- Flask
- pandas
- PostgreSQL
- SQLAlchemy
- requests
- Render
- GitHub

## 主要功能

1. 公司名稱查詢
2. 公開違反勞動法令紀錄列表
3. 違規類型分類
4. 縣市與資料來源統計
5. 重複出現事業單位統計
6. Render PostgreSQL 部署
7. 資料處理流程說明

## 本機執行

```bash
pip install -r requirements.txt
python scripts/init_db.py
python app.py