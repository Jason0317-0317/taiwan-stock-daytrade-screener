from datetime import datetime

import pandas as pd

from email_report import render_email_report


def sample_rankings():
    return pd.DataFrame(
        [
            {
                "rank": 1,
                "symbol": "2330",
                "name": "台積電",
                "price": 1500.0,
                "avg_vol": 12000.0,
                "avg_amt": 18_000_000_000.0,
                "avg_amp": 0.045,
                "vol_ratio": 1.8,
                "ret_5": 0.08,
                "ret_20": 0.12,
                "total_score": 2.1,
                "volatility_factor": 1.4,
                "liquidity_factor": 2.0,
                "momentum_factor": 1.8,
                "chip_factor": -0.2,
                "reason": "成交金額大、近5日動能強",
            },
            {
                "rank": 2,
                "symbol": "2454",
                "name": "聯發科 <測試>",
                "price": 1300.0,
                "avg_vol": 8000.0,
                "avg_amt": 9_000_000_000.0,
                "avg_amp": 0.052,
                "vol_ratio": 1.3,
                "ret_5": -0.01,
                "ret_20": 0.05,
                "total_score": 1.2,
                "volatility_factor": 1.8,
                "liquidity_factor": 1.1,
                "momentum_factor": 0.4,
                "chip_factor": 0.3,
                "reason": "20日平均振幅高",
            },
        ]
    )


def test_render_email_report_creates_individual_cards_and_charts():
    ranked = sample_rankings()

    report = render_email_report(
        ranked,
        ranked,
        generated_at=datetime(2026, 7, 21, 4, 0),
    )

    assert "台股隔日當沖候選報告" in report
    assert "綜合分數排名圖" in report
    assert "個股判讀卡片" in report
    assert "#1" in report and "#2" in report
    assert "2330 台積電" in report
    assert "聯發科 &lt;測試&gt;" in report
    assert "波動因子" in report
    assert "流動性因子" in report
    assert "動能因子" in report
    assert "籌碼因子" in report
    assert "18,000.00" not in report
    assert "180.00 億" in report


def test_render_email_report_handles_empty_result():
    empty = pd.DataFrame()

    report = render_email_report(
        empty,
        empty,
        generated_at=datetime(2026, 7, 21, 4, 0),
    )

    assert "今日沒有符合條件的股票" in report
    assert "報告股票數" in report
