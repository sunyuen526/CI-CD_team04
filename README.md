# 記帳追蹤系統 (Expense Tracker)

這是一個由兩人透過 Git 協作開發的 Python 網頁版記帳應用程式，介面簡潔直覺。
使用者可以隨時新增與管理日常支出，透過日期、月份、類別與關鍵字進行篩選，匯出 CSV 報表，並藉由圓餅圖（甜甜圈圖）、長條圖與每月趨勢圖掌握花費分佈。

## 功能特色

* **新增與驗證支出**：記錄支出的日期、金額（支援整數或最多一位小數）、類別與選填備註，並內建輸入格式驗證
* **一鍵刪除紀錄**：可直接從網頁明細表中點擊按鈕並確認刪除錯誤的支出項目
* **彈性時間篩選**：支援切換**全部（All）**紀錄、**今日（Today）**快捷檢視、指定**特定日期（Date）**或**月份（Month）**下拉篩選
* **類別與關鍵字搜尋**：可依消費類別或備註關鍵字過濾明細，上方統計卡片與圖表會即時同步更新
* **匯出 CSV 報表**：點擊 `Export CSV` 即可下載符合目前篩選條件的明細檔案（採用 UTF-8 BOM 編碼，Windows Excel 開啟中文不亂碼）
* **互動式視覺化圖表**：提供**圓餅圖（Donut chart）**、**長條圖（Bar chart）**與**每月支出趨勢圖（Monthly trend）**，完整支援中文類別顯示
* **純文字 CSV 儲存**：所有記帳資料皆儲存於本地端的 `expenses.csv`，方便備份與查閱

## 專案架構與分工

| 檔案名稱 | 功能說明 | 負責人 |
| :--- | :--- | :--- |
| `expense_input.py` | 驗證、儲存與刪除 `expenses.csv` 中的支出資料（亦支援終端機命令列輸入） | hsisophia |
| `expense_app.py` | 網頁版使用者介面、時間/類別/關鍵字篩選與 CSV 匯出（僅使用 Python 標準庫） | hsisophia & sunyuen526 |
| `expense_chart.py` | 繪製各類別消費比例圓餅圖與金額長條圖（支援中文字型與一位小數顯示） | sunyuen526 |
| `expense_trend.py` | 繪製跨月份總支出趨勢長條圖 | hsisophia |
| `sample_expenses.csv` | 內建範例測試資料集 | - |
| `requirements.txt` | 專案所需套件清單（`matplotlib`） | sunyuen526 |

## 環境建置

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 執行方式

### 方式一：網頁版介面（推薦）

```bash
python expense_app.py
```

執行後瀏覽器會自動開啟 http://127.0.0.1:8000。在左側表單填寫日期、金額、類別與備註後點擊 **Add expense** 即可新增。
圖表上方可使用 **All**、**Today**、**Date** 或 **Month** 切換時間範圍；下方表格可依類別與關鍵字搜尋、點擊 **Export CSV** 下載篩選結果，或點擊 **Delete** 刪除單筆資料。
使用完畢後，在終端機按 `Ctrl+C` 即可停止伺服器。

### 方式二：命令列模式（Command line）

```bash
python expense_input.py                        # 在終端機互動式新增支出（存入 expenses.csv）
python expense_chart.py                        # 輸出圓餅圖 pie_chart.png 與長條圖 bar_chart.png
python expense_trend.py                        # 輸出趨勢圖 trend_chart.png
python expense_chart.py sample_expenses.csv    # 使用內建範例資料測試圖表生成
```

所有資料皆儲存於 `expenses.csv`（欄位格式：`date, amount, category, notes`）。

## 範例輸出圖表

![Sample pie chart](sample_pie_chart.png)

![Sample bar chart](sample_bar_chart.png)

## 常見問題排解

* **圖表中的中文字顯示為方框（亂碼）：** 請確認已透過 `git pull` 更新至最新版本，Windows 環境下程式會自動套用微軟正黑體（Microsoft JhengHei）。
* **網頁無法連線（`ERR_CONNECTION_REFUSED`）：** 請先在終端機執行 `python expense_app.py` 啟動伺服器，並在使用期間保持終端機視窗開啟。

## Git 協作開發流程

本專案採用獨立功能分支（Feature Branch）開發，並透過 Pull Request 進行程式碼審查（Code Review）後合併至 `main` 分支（包含 `feature-input`、`feature-piechart`、`fix-chinese-font`、`feature-delete`、`feature-month-filter`、`feature-trend`、`feature-filters-export`）。
完整的分支與合併歷程可於 GitHub 倉庫頁面的 **Insights -> Network** 中檢視。

## 系統操作展示影片

https://youtu.be/aygy1tZ6S7E?si=ssbAW9agvJ2NuKmS


77777777777777777777777777777777777777777
66666666666666666666666666666666666666666