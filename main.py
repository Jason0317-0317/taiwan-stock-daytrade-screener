import pandas as pd
from get_stock_list import get_stock_list
from quant_analysis import download_batch, score_and_rank
from datetime import datetime

def main():
    print(f"--- 台股當沖量化篩選啟動 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---")
    
    # 1. 獲取股票清單
    print("正在獲取上市櫃股票清單...")
    df_info = get_stock_list()
    print(f"共找到 {len(df_info)} 檔普通股。")
    
    # 2. 下載數據並執行第一層篩選 (流動性前20%)
    # 提示：為了演示速度，此處取前 500 檔。如需全市場請改為 df_info
    print("正在下載歷史數據並執行流動性篩選...")
    df_res = download_batch(df_info.iloc[:500])
    
    # 3. 計算因子加權平均分數與排名
    print("正在計算因子加權平均分數...")
    df_ranked = score_and_rank(df_res)
    
    # 4. 只輸出前 10 名，作為每日 email 附件
    output_file = "final_rankings.csv"
    top_10 = df_ranked.head(10)
    top_10.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    print("\n--- 最值得優先關注的前 10 名股票 ---")
    if top_10.empty:
        print("今日沒有符合條件的股票。")
    else:
        print(top_10[['symbol', 'name', 'price', 'total_score']])
    
    print(f"\n前 10 名數據已儲存至: {output_file}")
    print(f"完整候選數量: {len(df_ranked)}；email 附件只包含前 10 名。")

if __name__ == "__main__":
    main()
