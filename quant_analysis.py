import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def get_stock_data():
    df_info = pd.read_csv("/home/ubuntu/raw_stock_list.csv")
    return df_info

def download_batch(df_info):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=40)
    
    symbols = df_info['symbol'].astype(str).tolist()
    yf_symbols = []
    sym_map = {}
    
    for _, row in df_info.iterrows():
        s = str(row['symbol'])
        yf_sym = f"{s}.TW" if row['market'] == '上市' else f"{s}.TWO"
        yf_symbols.append(yf_sym)
        sym_map[yf_sym] = {'symbol': s, 'name': row['name']}

    print(f"Downloading data for {len(yf_symbols)} stocks...")
    data = yf.download(yf_symbols, start=start_date, end=end_date, group_by='ticker', threads=True, progress=True)
    
    all_stocks_stats = []
    for yf_sym in yf_symbols:
        try:
            df = data[yf_sym]
            if df.empty or len(df) < 25: continue
            
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']
            if close.isnull().all(): continue
                
            amount = close * volume
            amplitude = (high - low) / close.shift(1)
            
            avg_volume_20 = volume.rolling(window=20).mean().iloc[-1]
            avg_amount_20 = amount.rolling(window=20).mean().iloc[-1]
            avg_amplitude_20 = amplitude.rolling(window=20).mean().iloc[-1]
            current_price = close.iloc[-1]
            
            # 儲存所有股票的統計數據以便後續計算百分位數
            all_stocks_stats.append({
                'yf_sym': yf_sym,
                'symbol': sym_map[yf_sym]['symbol'],
                'name': sym_map[yf_sym]['name'],
                'price': current_price,
                'avg_vol': avg_volume_20,
                'avg_amt': avg_amount_20,
                'avg_amp': avg_amplitude_20,
                'df': df # 暫存以供後續因子計算
            })
        except Exception:
            continue
            
    df_stats = pd.DataFrame(all_stocks_stats)
    if df_stats.empty: return df_stats
    
    # 計算百分位數門檻 (前20% 即 80th percentile)
    vol_threshold = df_stats['avg_vol'].quantile(0.8)
    amt_threshold = df_stats['avg_amt'].quantile(0.8)
    
    print(f"Volume Threshold (Top 20%): {vol_threshold:.0f}")
    print(f"Amount Threshold (Top 20%): {amt_threshold:.0f}")
    
    results = []
    for _, row in df_stats.iterrows():
        # 第一層篩選：動態百分位數 + 振幅 + 股價
        if row['avg_vol'] < vol_threshold: continue
        if row['avg_amt'] < amt_threshold: continue
        if row['avg_amp'] < 0.04: continue
        if row['price'] < 20 or row['price'] > 500: continue
        
        df = row['df']
        close = df['Close']
        volume = df['Volume']
        
        # 第二層因子
        ret_5 = (close.iloc[-1] / close.iloc[-6]) - 1
        ret_20 = (close.iloc[-1] / close.iloc[-21]) - 1
        vol_ratio = volume.iloc[-1] / row['avg_vol']
        chip_proxy = (ret_5 * 0.4 + (vol_ratio - 1) * 0.6)
        
        results.append({
            'symbol': row['symbol'],
            'name': row['name'],
            'price': row['price'],
            'avg_vol': row['avg_vol'],
            'avg_amt': row['avg_amt'],
            'avg_amp': row['avg_amp'],
            'ret_5': ret_5,
            'ret_20': ret_20,
            'vol_ratio': vol_ratio,
            'chip_proxy': chip_proxy
        })
            
    return pd.DataFrame(results)

def score_and_rank(df):
    if df.empty: return df
    factors = ['avg_amp', 'vol_ratio', 'ret_5', 'chip_proxy']
    for f in factors:
        df[f'{f}_z'] = (df[f] - df[f].mean()) / df[f].std()
    
    df['total_score'] = (
        df['avg_amp_z'] * 0.30 +
        df['vol_ratio_z'] * 0.25 +
        df['ret_5_z'] * 0.25 +
        df['chip_proxy_z'] * 0.20
    )
    return df.sort_values(by='total_score', ascending=False)

if __name__ == "__main__":
    df_info = get_stock_data()
    # 執行前 1000 檔作為範例
    df_res = download_batch(df_info.iloc[:1000])
    df_ranked = score_and_rank(df_res)
    df_ranked.to_csv("/home/ubuntu/final_rankings.csv", index=False)
    print(f"Ranking completed. Found {len(df_ranked)} candidates.")
