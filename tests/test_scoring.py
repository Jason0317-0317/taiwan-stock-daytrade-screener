import pandas as pd

from quant_analysis import apply_candidate_exclusions


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
