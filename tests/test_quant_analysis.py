from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from quant_analysis import (
    DataQualityError,
    _clean_price_frame,
    _is_recent_trading_data,
    score_and_rank,
)


def sample_candidates(count=12, chip=False):
    rows = []
    for index in range(count):
        strength = index + 1
        rows.append(
            {
                "symbol": f"{1000 + index}",
                "name": f"Stock {index}",
                "price": 30.0 + index,
                "avg_vol": 6_000.0 + strength * 100,
                "avg_amt": 600_000_000.0 + strength * 1_000_000,
                "avg_amp": 0.04 + strength / 1000,
                "atr_14": 2.0 + strength / 10,
                "atr_pct": 0.03 + strength / 1000,
                "ret_1": strength / 1000,
                "ret_3": strength / 500,
                "ret_5": strength / 400,
                "ret_20": strength / 300,
                "vol_ratio": 1.0 + strength / 20,
                "vol_3_ratio": 1.0 + strength / 15,
                "close_position_20": 0.4 + strength / 30,
                "main_buy_5d": strength if chip else 0,
                "foreign_buy_5d": strength if chip else 0,
                "investment_trust_buy_5d": strength if chip else 0,
                "margin_change_pct": strength / 1000 if chip else 0,
                "short_change_pct": -strength / 1000 if chip else 0,
                "data_date": "2026-07-29",
            }
        )
    return pd.DataFrame(rows)


def test_score_and_rank_uses_short_term_factors_and_disables_missing_chip_data():
    ranked = score_and_rank(sample_candidates())

    assert ranked.iloc[0]["symbol"] == "1011"
    assert ranked["total_score"].is_monotonic_decreasing
    assert not ranked["chip_data_available"].any()
    assert (ranked["chip_factor"] == 0).all()
    assert {
        "atr_pct_z",
        "ret_1_z",
        "ret_3_z",
        "vol_3_ratio_z",
        "close_position_20_z",
        "short_term_factor",
    }.issubset(ranked.columns)


def test_score_and_rank_enables_chip_factor_when_data_exists():
    ranked = score_and_rank(sample_candidates(chip=True))

    assert ranked["chip_data_available"].all()
    assert ranked["chip_factor"].abs().sum() > 0


def test_score_and_rank_rejects_nan_instead_of_silently_scoring_it():
    candidates = sample_candidates()
    candidates.loc[0, "price"] = np.nan

    with pytest.raises(DataQualityError, match="price"):
        score_and_rank(candidates)


def test_score_and_rank_rejects_too_few_candidates():
    with pytest.raises(DataQualityError, match="minimum"):
        score_and_rank(sample_candidates(count=5))


def test_clean_price_frame_drops_partial_latest_row():
    index = pd.date_range("2026-07-27", periods=3, freq="D")
    frame = pd.DataFrame(
        {
            "Open": [100, 101, 102],
            "High": [102, 103, 104],
            "Low": [99, 100, 101],
            "Close": [101, 102, np.nan],
            "Volume": [1_000, 1_100, 1_200],
        },
        index=index,
    )

    clean = _clean_price_frame(frame)

    assert clean.index[-1] == pd.Timestamp("2026-07-28")
    assert clean.notna().all().all()


def test_recent_data_check_rejects_stale_market_data():
    frame = pd.DataFrame(index=[pd.Timestamp("2026-07-20")])

    assert not _is_recent_trading_data(frame, now=datetime(2026, 7, 30))
