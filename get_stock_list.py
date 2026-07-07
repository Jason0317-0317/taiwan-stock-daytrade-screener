import twstock
import pandas as pd

def get_stock_list():
    stocks = []
    for code, info in twstock.codes.items():
        # 過濾普通股 (type 為 '股票')
        if info.type == '股票':
            stocks.append({
                'symbol': info.code,
                'name': info.name,
                'market': info.market,
                'industry': info.group,
                'isin': info.ISIN
            })
    return pd.DataFrame(stocks)

if __name__ == "__main__":
    df_stocks = get_stock_list()
    # 確保代號是4碼
    df_stocks = df_stocks[df_stocks['symbol'].str.len() == 4]
    df_stocks.to_csv("/home/ubuntu/raw_stock_list.csv", index=False)
    print(f"Total stocks found: {len(df_stocks)}")
