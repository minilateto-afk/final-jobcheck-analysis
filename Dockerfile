# 使用 Python 3.12 slim 作為基礎映像
FROM python:3.12-slim

# 設定容器內工作目錄
WORKDIR /app

# 複製套件需求檔
COPY requirements.txt .

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案到容器內
COPY . .

# 開放 Flask 預設 port
EXPOSE 5000

# 啟動 Flask 主程式
CMD ["python", "app.py"]