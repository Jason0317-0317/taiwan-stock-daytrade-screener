# 台股隔日當沖量化篩選系統

這是一個 Python 量化篩選工具，用來從所有上市櫃個股中，依照流動性、波動性、動能與籌碼因子，產生隔日當沖候選名單前 10 名。

此專案是盤前觀察工具，不是自動下單系統，也不構成投資建議。

## 系統架構

1. `get_stock_list.py`: 從 `twstock` 取得上市櫃普通股清單。
2. `quant_analysis.py`: 核心分析腳本。
   - 排除 ETF、ETN、TDR，以及停牌、全額交割、處置股清單。
   - 依照 20 日均量、20 日均成交金額、20 日平均振幅與股價區間建立候選池。
   - 計算報酬率、振幅、ATR、量能倍率、籌碼與信用交易因子。
   - 對所有因子進行 Z-score 標準化。
   - 依四大因子權重計算 `total_score`。
3. `main.py`: 整合執行入口，產出前 10 名 CSV 與 HTML 分析報告。
4. `email_report.py`: 產生 Email 相容的排名圖、因子圖與個股判讀卡片。
5. `.github/workflows/daily-email.yml`: 週一至週五自動產生報告並寄出 HTML email。

## 第一層：候選池篩選

系統會先排除：

- 停牌股票
- 全額交割股
- 處置股
- ETF
- ETN
- TDR
- 最近 20 個交易日平均成交量低於 5,000 張者
- 最近 20 個交易日平均成交金額低於 5 億元者
- 最近 20 個交易日平均振幅低於 4% 者
- 股價低於 20 元或高於 500 元者

停牌、全額交割、處置股可透過下列檔案提供：

```text
data/suspended.csv
data/full_delivery.csv
data/disposition.csv
```

每個檔案至少需包含 `symbol`、`code`、`股票代號` 或 `證券代號` 其中一個欄位。

## 第二層：因子計算

通過候選池後會計算：

- 近 5 日報酬率 `ret_5`
- 近 20 日報酬率 `ret_20`
- 近 20 日平均振幅 `avg_amp`
- ATR(14) `atr_14`
- 成交量相對於 20 日均量倍率 `vol_ratio`
- 近 5 日主力買賣超 `main_buy_5d`
- 外資近 5 日買賣超 `foreign_buy_5d`
- 投信近 5 日買賣超 `investment_trust_buy_5d`
- 融資增減幅 `margin_change_pct`
- 融券增減幅 `short_change_pct`

籌碼與信用交易資料可透過 `data/chip_factors.csv` 提供。若尚未提供，程式會以 0 補齊，讓每日排程仍可產出價格與量能版本的候選名單。

`data/chip_factors.csv` 建議格式：

```csv
symbol,main_buy_5d,foreign_buy_5d,investment_trust_buy_5d,margin_change_pct,short_change_pct
2330,12000,8500,2200,0.03,-0.02
```

## 第三層：綜合評分

所有原始因子會先做 Z-score 標準化，再合成四大類別分數：

| 類別 | 組成 | 權重 |
|---|---|---:|
| 波動因子 | `avg_amp_z`, `atr_14_z` | 30% |
| 流動性因子 | `avg_vol_z`, `avg_amt_z`, `vol_ratio_z` | 25% |
| 動能因子 | `ret_5_z`, `ret_20_z` | 25% |
| 籌碼因子 | 主力、外資、投信、融資、融券反向分數 | 20% |

公式：

```text
Total Score =
波動因子 * 0.30
+ 流動性因子 * 0.25
+ 動能因子 * 0.25
+ 籌碼因子 * 0.20
```

`total_score` 越高代表在候選股票中的綜合排名越前面。

## 輸出結果

執行完成後會產出：

- `final_rankings.csv`: 前 10 名排名、因子數據與主要加分原因。
- `report.html`: 直接作為 Email 正文，包含市場摘要、綜合分數排名圖，以及每檔股票獨立的判讀卡片。
  - 個股價格、20 日均量、平均成交金額與平均振幅
  - 當日量比、5 日／20 日動能
  - 波動、流動性、動能與籌碼四大因子圖
  - 入選原因與風險提醒
- 控制台報告：
  - 前 10 名平均成交量
  - 前 10 名平均振幅
  - 前 10 名平均成交金額
  - 市場整體強弱評估
  - 隔日當沖風險提醒
  - 最值得優先關注的前 3 名股票與入選原因

## 自動寄信時間

GitHub Actions 目前設定為週一至週五台灣時間早上 04:00 執行；週六、週日不執行也不寄信。Email 會直接顯示 HTML 分析報告，並附上 CSV 與 HTML 檔案供下載。

```yaml
cron: "0 20 * * 0-4"
```

GitHub Actions 使用 UTC 時區，因此週日至週四的 `20:00 UTC`，等於台灣時間週一至週五的 `04:00`。

## 安裝需求

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python main.py
```

## 注意事項

- 此工具僅供量化研究與交易前觀察，不構成投資建議。
- `yfinance` 資料可能受網路、延遲與資料源穩定性影響。
- 停牌、全額交割、處置股、籌碼與信用交易資料需要定期更新，才會完整符合策略規格。
