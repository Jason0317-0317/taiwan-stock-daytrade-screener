# 台股隔日當沖量化篩選系統

這是一個基於 Python 的量化交易篩選工具，旨在從台股所有上市櫃股票中，根據流動性、波動性、動能及籌碼因子，篩選出最適合隔日當沖的前 10 名標的。

## 系統架構

1. `get_stock_list.py`: 從 twstock 取得上市櫃普通股清單。
2. `quant_analysis.py`: 核心分析腳本。
   - 自動計算成交量與成交金額的百分位數。
   - 篩選前 20% 流動性標的。
   - 將振幅、量能放大、5 日動能、籌碼代理因子轉成百分位分數。
   - 使用加權平均產生 0-100 的 `total_score`。
3. `main.py`: 整合執行入口，產出前 10 名 CSV 排名與分析報告。
4. `.github/workflows/daily-email.yml`: 每天自動產生報告並寄出 email。

## 評分方式

目前總分採用百分位數加權平均：

| 因子 | 權重 |
|---|---:|
| 20 日平均振幅 `avg_amp` | 30% |
| 當日量能放大倍數 `vol_ratio` | 25% |
| 5 日報酬率 `ret_5` | 25% |
| 籌碼代理因子 `chip_proxy` | 20% |

`total_score` 越高代表在候選股票中的綜合排名越前面。

## 自動寄信時間

GitHub Actions 目前設定為每天台灣時間早上 04:00 執行。

```yaml
cron: "0 20 * * *"
```

GitHub Actions 使用 UTC 時區，因此 `20:00 UTC` 等於台灣時間隔天 `04:00`。

## 通知內容

- 程式目前會分析股票清單中的前 500 檔。
- 篩選後只輸出前 10 名到 `final_rankings.csv`，並作為 email 附件寄出。
- 控制台會輸出前 10 名優先關注標的與完整候選數量。

## 安裝需求

請確保您的環境已安裝以下 Python 套件：

```bash
pip install pandas numpy yfinance twstock requests
```

或直接使用：

```bash
pip install -r requirements.txt
```

## 使用方法

直接執行 `main.py` 即可：

```bash
python main.py
```

執行完成後，系統會產出：

- `final_rankings.csv`: 前 10 名排名與因子數據。
- 控制台前 10 名推薦名單與市場分析。

## 注意事項

- 此工具僅供量化研究與交易前觀察，不構成投資建議。
- yfinance 資料可能受網路與資料源穩定性影響。
- 若要分析全市場，可將 `main.py` 中的 `df_info.iloc[:500]` 改為 `df_info`。
