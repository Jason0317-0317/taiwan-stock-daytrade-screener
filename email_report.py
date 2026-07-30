from __future__ import annotations

import html
from datetime import datetime

import pandas as pd

from quant_analysis import market_strength_summary


FACTOR_ROWS = (
    ("波動因子", "volatility_factor"),
    ("流動性因子", "liquidity_factor"),
    ("中期動能", "momentum_factor"),
    ("短期訊號", "short_term_factor"),
    ("籌碼因子", "chip_factor"),
)


def _number(value, default=0.0) -> float:
    try:
        result = float(value)
        return result if pd.notna(result) else default
    except (TypeError, ValueError):
        return default


def _factor_bar(value) -> str:
    score = _number(value)
    width = min(100, max(3, abs(score) / 3 * 100))
    color = "#0f9d7a" if score >= 0 else "#dc5a5a"
    return (
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
        'style="border-collapse:collapse"><tr>'
        '<td style="background:#e8edf3;height:8px;border-radius:4px">'
        f'<div style="width:{width:.0f}%;height:8px;background:{color};border-radius:4px"></div>'
        "</td></tr></table>"
    )


def _score_chart(top_10: pd.DataFrame) -> str:
    if top_10.empty:
        return '<p style="color:#687386">今日沒有符合條件的股票。</p>'
    max_score = max(abs(_number(x)) for x in top_10["total_score"]) or 1
    rows = []
    for _, row in top_10.iterrows():
        score = _number(row.get("total_score"))
        width = max(4, abs(score) / max_score * 100)
        color = "#176b87" if score >= 0 else "#c45b5b"
        label = html.escape(f"{row.get('symbol', '')} {row.get('name', '')}")
        rows.append(
            '<tr><td style="padding:5px 10px 5px 0;width:145px;font-size:13px">'
            f'{label}</td><td style="padding:5px 0">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0">'
            '<tr><td style="background:#e8edf3;height:12px;border-radius:6px">'
            f'<div style="width:{width:.0f}%;height:12px;background:{color};border-radius:6px"></div>'
            "</td></tr></table></td>"
            f'<td style="padding:5px 0 5px 10px;width:54px;text-align:right;font-weight:bold">{score:+.2f}</td></tr>'
        )
    return '<table role="presentation" width="100%" cellspacing="0" cellpadding="0">' + "".join(rows) + "</table>"


def _metric(label: str, value: str) -> str:
    return (
        '<td width="33.33%" style="padding:6px">'
        '<div style="background:#f4f7fa;border-radius:8px;padding:10px">'
        f'<div style="font-size:11px;color:#718096">{html.escape(label)}</div>'
        f'<div style="font-size:17px;font-weight:bold;margin-top:3px">{html.escape(value)}</div>'
        "</div></td>"
    )


def _stock_card(row: pd.Series) -> str:
    rank = int(_number(row.get("rank")))
    symbol = html.escape(str(row.get("symbol", "")))
    name = html.escape(str(row.get("name", "")))
    score = _number(row.get("total_score"))
    reason = html.escape(str(row.get("reason", "綜合條件相對均衡")))

    factor_rows = []
    chip_available = bool(row.get("chip_data_available", False))
    weights = (
        {
            "volatility_factor": "20%",
            "liquidity_factor": "20%",
            "momentum_factor": "20%",
            "short_term_factor": "25%",
            "chip_factor": "15%",
        }
        if chip_available
        else {
            "volatility_factor": "25%",
            "liquidity_factor": "25%",
            "momentum_factor": "20%",
            "short_term_factor": "30%",
            "chip_factor": "停用",
        }
    )
    for label, column in FACTOR_ROWS:
        value = _number(row.get(column))
        weight = weights[column]
        factor_rows.append(
            '<tr><td style="padding:5px 8px 5px 0;width:88px;font-size:12px">'
            f'{label}</td><td style="padding:5px 8px">{_factor_bar(value)}</td>'
            f'<td style="padding:5px 0;width:70px;text-align:right;font-size:12px">{value:+.2f} · {weight}</td></tr>'
        )

    metrics_1 = "".join(
        (
            _metric("收盤價", f"{_number(row.get('price')):,.2f} 元"),
            _metric("20 日均量", f"{_number(row.get('avg_vol')):,.0f} 張"),
            _metric("20 日均成交額", f"{_number(row.get('avg_amt')) / 100_000_000:,.2f} 億"),
        )
    )
    metrics_2 = "".join(
        (
            _metric("20 日平均振幅", f"{_number(row.get('avg_amp')):.2%}"),
            _metric("當日量比", f"{_number(row.get('vol_ratio')):.2f} 倍"),
            _metric("1 日／3 日動能", f"{_number(row.get('ret_1')):+.2%} / {_number(row.get('ret_3')):+.2%}"),
        )
    )

    return f"""
    <div style="border:1px solid #dce3ea;border-radius:12px;margin:18px 0;background:#ffffff;overflow:hidden">
      <div style="padding:14px 16px;background:#f8fafc;border-bottom:1px solid #e4e9ef">
        <table role="presentation" width="100%"><tr>
          <td><span style="display:inline-block;background:#176b87;color:#fff;border-radius:20px;padding:5px 10px;font-weight:bold">#{rank}</span>
          <span style="font-size:19px;font-weight:bold;margin-left:8px">{symbol} {name}</span></td>
          <td style="text-align:right"><span style="font-size:12px;color:#718096">綜合分數</span><br>
          <span style="font-size:21px;font-weight:bold;color:#176b87">{score:+.2f}</span></td>
        </tr></table>
      </div>
      <div style="padding:10px">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr>{metrics_1}</tr><tr>{metrics_2}</tr></table>
      </div>
      <div style="padding:4px 16px 12px">
        <div style="font-size:13px;font-weight:bold;margin-bottom:4px">四大因子輔助圖</div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">{''.join(factor_rows)}</table>
        <div style="background:#eef7f5;border-left:4px solid #0f9d7a;padding:10px 12px;margin-top:10px;font-size:13px">
          <strong>入選原因：</strong>{reason}
        </div>
      </div>
    </div>"""


def render_email_report(
    top_10: pd.DataFrame,
    df_ranked: pd.DataFrame,
    generated_at: datetime | None = None,
) -> str:
    generated_at = generated_at or datetime.now()
    market_summary = html.escape(market_strength_summary(df_ranked))
    avg_amp = _number(top_10["avg_amp"].mean()) if not top_10.empty else 0
    avg_amount = _number(top_10["avg_amt"].mean()) / 100_000_000 if not top_10.empty else 0
    positive_5d = _number((top_10["ret_5"] > 0).mean()) if not top_10.empty else 0
    data_date = (
        str(top_10["data_date"].max())
        if not top_10.empty and "data_date" in top_10.columns
        else "未知"
    )
    chip_status = (
        "已啟用"
        if not top_10.empty and bool(top_10.iloc[0].get("chip_data_available", False))
        else "無資料，已停用"
    )
    cards = "".join(_stock_card(row) for _, row in top_10.iterrows())
    if not cards:
        cards = '<div style="padding:24px;background:#fff;border-radius:10px">今日沒有符合條件的股票。</div>'

    return f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#edf2f6;color:#182433;font-family:Arial,'Noto Sans TC','Microsoft JhengHei',sans-serif">
  <div style="max-width:760px;margin:0 auto;padding:20px 12px">
    <div style="background:linear-gradient(135deg,#0f4c5c,#176b87);color:#fff;border-radius:14px;padding:22px">
      <div style="font-size:12px;opacity:.85">盤前量化觀察 · {generated_at:%Y-%m-%d %H:%M}</div>
      <h1 style="font-size:25px;margin:7px 0">台股隔日當沖候選報告</h1>
      <div style="font-size:14px;line-height:1.6">{market_summary}</div>
    </div>

    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:12px 0"><tr>
      {_metric("完整候選數", f"{len(df_ranked)} 檔")}
      {_metric("前十平均振幅", f"{avg_amp:.2%}")}
      {_metric("前十平均成交額", f"{avg_amount:,.2f} 億")}
    </tr><tr>
      {_metric("前十 5 日動能為正", f"{positive_5d:.0%}")}
      {_metric("資料交易日", data_date)}
      {_metric("籌碼因子", chip_status)}
    </tr></table>

    <div style="background:#fff;border-radius:12px;padding:16px;margin:14px 0">
      <h2 style="font-size:17px;margin:0 0 10px">綜合分數排名圖</h2>
      {_score_chart(top_10)}
    </div>

    <h2 style="font-size:19px;margin:22px 2px 8px">個股判讀卡片</h2>
    {cards}

    <div style="background:#fff4e5;border-left:4px solid #e69a2d;padding:12px 14px;margin-top:18px;font-size:13px;line-height:1.6">
      <strong>風險提醒：</strong>本名單僅供盤前觀察，不構成投資建議。隔日當沖仍須留意開盤跳空、流動性急縮、處置風險、交易成本與停損紀律。因子條越長代表該因子偏離候選池平均越多；綠色為正向、紅色為負向。
    </div>
    <p style="color:#718096;font-size:11px;text-align:center;margin:18px 0">CSV 詳細資料仍附於信件，可供另行分析。</p>
  </div>
</body></html>"""
