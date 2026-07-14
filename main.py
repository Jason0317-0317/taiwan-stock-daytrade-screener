from datetime import datetime

from get_stock_list import get_stock_list
from quant_analysis import download_batch, market_strength_summary, score_and_rank


def print_report(top_10, df_ranked):
    print("\n--- 最值得優先關注的前 10 名股票 ---")
    if top_10.empty:
        print("今日沒有符合條件的股票。")
        return

    display_cols = ["rank", "symbol", "name", "price", "total_score", "reason"]
    print(top_10[display_cols].to_string(index=False))

    print("\n--- 前 10 名統計 ---")
    print(f"平均成交量: {top_10['avg_vol'].mean():,.0f} 張")
    print(f"平均振幅: {top_10['avg_amp'].mean():.2%}")
    print(f"平均成交金額: {top_10['avg_amt'].mean():,.0f} 元")
    print(market_strength_summary(df_ranked))

    print("\n--- 隔日當沖風險提醒 ---")
    print("此名單僅供盤前觀察，不構成投資建議。隔日當沖仍需留意開盤跳空、流動性急縮、處置風險與停損紀律。")

    print("\n--- 最值得優先關注的前 3 名股票 ---")
    for _, row in top_10.head(3).iterrows():
        print(f"{int(row['rank'])}. {row['symbol']} {row['name']}: {row['reason']}，綜合分數 {row['total_score']:.2f}。")


def main():
    print(f"--- 台股隔日當沖量化篩選啟動 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---")

    print("正在獲取上市櫃股票清單...")
    df_info = get_stock_list()
    print(f"共找到 {len(df_info)} 檔普通股。")

    print("正在下載歷史數據並執行第一層候選池篩選...")
    df_res = download_batch(df_info)

    print("正在執行 Z-score 標準化與四大因子加權評分...")
    df_ranked = score_and_rank(df_res)

    if not df_ranked.empty:
        df_ranked["rank"] = range(1, len(df_ranked) + 1)

    output_file = "final_rankings.csv"
    top_10 = df_ranked.head(10)
    top_10.to_csv(output_file, index=False, encoding="utf-8-sig")

    print_report(top_10, df_ranked)

    print(f"\n前 10 名數據已儲存至: {output_file}")
    print(f"完整候選數量: {len(df_ranked)}；email 附件只包含前 10 名。")


if __name__ == "__main__":
    main()
