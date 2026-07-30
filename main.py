from datetime import datetime
import html
import os

import pandas as pd

from email_report import render_email_report
from get_stock_list import get_stock_list
from quant_analysis import (
    DataQualityError,
    download_batch,
    market_strength_summary,
    score_and_rank,
)


def _set_report_status(status):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"report_status={status}\n")


def _write_quality_alert(message):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    alert_html = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"></head>
<body style="font-family:Arial,'Microsoft JhengHei',sans-serif;background:#f6f7f9;color:#222;padding:24px">
  <div style="max-width:680px;margin:auto;background:#fff;border-left:6px solid #c0392b;padding:24px">
    <h1 style="color:#c0392b">台股報告資料異常</h1>
    <p>本次資料未通過品質檢查，因此沒有產生或寄送股票排名。</p>
    <p><strong>異常原因：</strong>{html.escape(str(message))}</p>
    <p><strong>檢查時間：</strong>{generated_at}</p>
    <p>請檢查 Yahoo Finance 資料狀態及 GitHub Actions 執行紀錄。</p>
  </div>
</body></html>"""
    with open("report.html", "w", encoding="utf-8") as report:
        report.write(alert_html)
    pd.DataFrame(columns=["status", "message"]).to_csv(
        "final_rankings.csv", index=False, encoding="utf-8-sig"
    )
    _set_report_status("error")


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
    try:
        df_res = download_batch(df_info)

        print("正在執行資料品質檢查、Z-score 標準化與因子加權評分...")
        df_ranked = score_and_rank(df_res)
    except DataQualityError as exc:
        print(f"資料品質檢查失敗：{exc}")
        _write_quality_alert(exc)
        return

    if not df_ranked.empty:
        df_ranked["rank"] = range(1, len(df_ranked) + 1)

    output_file = "final_rankings.csv"
    top_10 = df_ranked.head(10)
    top_10.to_csv(output_file, index=False, encoding="utf-8-sig")

    report_file = "report.html"
    report_html = render_email_report(top_10, df_ranked)
    with open(report_file, "w", encoding="utf-8") as report:
        report.write(report_html)
    _set_report_status("ok")

    print_report(top_10, df_ranked)

    print(f"\n前 10 名數據已儲存至: {output_file}")
    print(f"HTML email 報告已儲存至: {report_file}")
    print(f"完整候選數量: {len(df_ranked)}；email 正文呈現前 10 名個股卡片，CSV 保留為附件。")


if __name__ == "__main__":
    main()
