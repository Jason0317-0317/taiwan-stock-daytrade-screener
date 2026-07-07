# 台股隔日當沖量化篩選系統

這是一個基於 Python 的量化交易篩選工具，旨在從台股所有上市櫃股票中，根據流動性、波動性、動能及籌碼因子，篩選出最適合隔日當沖的前 10 名標的。

## 系統架構

1.  `get_stock_list.py`: 從證交所獲取最新的上市櫃普通股清單。
2.  `quant_analysis.py`: 核心分析腳本。
    *   自動計算全市場成交量與成交金額的百分位數。
    *   篩選前 20% 流動性標的。
    *   計算 Z-score 標準化因子與綜合評分。
3.  `main.py`: 整合執行入口，產出最終 CSV 排名與分析報告。

## 安裝需求

請確保您的環境已安裝以下 Python 套件：

```bash
pip install pandas numpy yfinance twstock requests
```

## 使用方法

直接執行 `main.py` 即可：

```bash
python main.py
```

執行完成後，系統會產出：
*   `final_rankings.csv`: 完整的排名與因子數據。
*   控制台會輸出前 10 名推薦名單與市場分析。
