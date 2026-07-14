import pandas as pd

from quant_analysis import apply_candidate_exclusions, score_and_rank


def test_score_and_rank_uses_additive_weighted_factors():
    df = pd.DataFrame(
        [
            {
                "symbol": "1111",
                "name": "A",
                "price": 100,
                "avg_vol": 6000,
                "avg_amt": 600_000_000,
                "avg_amp": 0.05,
                "atr_14": 4,
                "ret_5": 0.05,
                "ret_20": 0.08,
                "vol_ratio": 2.0,
                "main_buy_5d": 100,
                "foreign_buy_5d": 100,
                "investment_trust_buy_5d": 100,
                "margin_change_pct": 0.02,
                "short_change_pct": -0.02,
            },
            {
                "symbol": "2222",
                "name": "B",
                "price": 100,
                "avg_vol": 5000,
                "avg_amt": 500_000_000,
                "avg_amp": 0.04,
                "atr_14": 2,
                "ret_5": -0.02,
                "ret_20": -0.03,
                "vol_ratio": 0.8,
                "main_buy_5d": -100,
                "foreign_buy_5d": -100,
                "investment_trust_buy_5d": -100,
                "margin_change_pct": -0.01,
                "short_change_pct": 0.03,
            },
        ]
    )

    ranked = score_and_rank(df)

    assert ranked.iloc[0]["symbol"] == "1111"
    assert ranked.iloc[0]["total_score"] > ranked.iloc[1]["total_score"]
    assert "reason" in ranked.columns


def test_apply_candidate_exclusions_removes_non_common_products():
    df = pd.DataFrame(
        [
            {"symbol": "2330", "name": "台積電", "market": "上市", "type": "股票"},
            {"symbol": "0050", "name": "元大台灣50 ETF", "market": "上市", "type": "ETF"},
            {"symbol": "9105", "name": "泰金寶-DR TDR", "market": "上市", "type": "股票"},
        ]
    )

    filtered = apply_candidate_exclusions(df)

    assert filtered["symbol"].tolist() == ["2330"]
