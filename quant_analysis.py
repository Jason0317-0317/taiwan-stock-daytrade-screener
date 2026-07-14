from datetime import datetime, timedelta
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")


MIN_AVG_VOLUME_LOTS = 5_000
MIN_AVG_AMOUNT = 500_000_000
MIN_AVG_AMPLITUDE = 0.04
MIN_PRICE = 20
MAX_PRICE = 500
DOWNLOAD_BATCH_SIZE = 80

CHIP_COLUMNS = [
    "main_buy_5d",
    "foreign_buy_5d",
    "investment_trust_buy_5d",
    "margin_change_pct",
    "short_change_pct",
]

CHIP_ALIASES = {
    "主力近5日買賣超": "main_buy_5d",
    "近5日主力買賣超": "main_buy_5d",
    "外資近5日買賣超": "foreign_buy_5d",
    "投信近5日買賣超": "investment_trust_buy_5d",
    "融資增減幅": "margin_change_pct",
    "融券增減幅": "short_change_pct",
}


def get_stock_data(path="raw_stock_list.csv"):
    return pd.read_csv(path)


def _read_symbol_file(path):
    if not path.exists():
        return set()

    df = pd.read_csv(path, dtype={"symbol": str})
    for col in ("symbol", "code", "股票代號", "證券代號"):
        if col in df.columns:
            return set(df[col].astype(str).str.strip())
    return set()


def load_exclusion_symbols(data_dir="data"):
    base = Path(data_dir)
    exclusion_files = [
        "suspended.csv",
        "full_delivery.csv",
        "disposition.csv",
    ]

    symbols = set()
    for filename in exclusion_files:
        symbols |= _read_symbol_file(base / filename)
    return symbols


def apply_candidate_exclusions(df_info, data_dir="data"):
    df = df_info.copy()
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["name"] = df["name"].astype(str)

    if "type" in df.columns:
        df = df[df["type"].astype(str).eq("股票")]

    security_text = df.astype(str).agg(" ".join, axis=1)
    blocked_keywords = r"ETF|ETN|TDR|指數股票型基金|指數投資證券|臺灣存託憑證|台灣存託憑證"
    df = df[~security_text.str.contains(blocked_keywords, case=False, regex=True)]
    df = df[df["symbol"].str.fullmatch(r"\d{4}", na=False)]

    excluded = load_exclusion_symbols(data_dir)
    if excluded:
        df = df[~df["symbol"].isin(excluded)]

    return df.reset_index(drop=True)


def load_chip_factors(data_dir="data"):
    path = Path(data_dir) / "chip_factors.csv"
    if not path.exists():
        return pd.DataFrame(columns=["symbol", *CHIP_COLUMNS])

    df = pd.read_csv(path, dtype={"symbol": str})
    df = df.rename(columns=CHIP_ALIASES)
    if "symbol" not in df.columns:
        return pd.DataFrame(columns=["symbol", *CHIP_COLUMNS])

    df["symbol"] = df["symbol"].astype(str).str.strip()
    for col in CHIP_COLUMNS:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df[["symbol", *CHIP_COLUMNS]]


def _ticker_symbol(row):
    symbol = str(row["symbol"]).strip()
    market = str(row.get("market", "上市"))
    suffix = ".TW" if market == "上市" else ".TWO"
    return f"{symbol}{suffix}"


def _get_ticker_frame(data, yf_symbol):
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        if yf_symbol not in data.columns.get_level_values(0):
            return pd.DataFrame()
        return data[yf_symbol].dropna(how="all")
    return data.dropna(how="all")


def _chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _atr(high, low, close, window=14):
    prev_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1).rolling(window=window).mean()


def download_batch(df_info, data_dir="data", limit=None):
    df_info = apply_candidate_exclusions(df_info, data_dir=data_dir)
    if limit:
        df_info = df_info.iloc[:limit]

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    yf_symbols = []
    symbol_map = {}
    for _, row in df_info.iterrows():
        yf_symbol = _ticker_symbol(row)
        yf_symbols.append(yf_symbol)
        symbol_map[yf_symbol] = {
            "symbol": str(row["symbol"]).strip(),
            "name": row["name"],
        }

    if not yf_symbols:
        return pd.DataFrame()

    chip_factors = load_chip_factors(data_dir)
    chip_by_symbol = chip_factors.set_index("symbol") if not chip_factors.empty else pd.DataFrame()

    results = []
    print(f"Downloading data for {len(yf_symbols)} stocks in batches of {DOWNLOAD_BATCH_SIZE}...")
    for batch_no, batch_symbols in enumerate(_chunks(yf_symbols, DOWNLOAD_BATCH_SIZE), start=1):
        print(f"Batch {batch_no}: {len(batch_symbols)} stocks")
        try:
            data = yf.download(
                batch_symbols,
                start=start_date,
                end=end_date,
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False,
            )
        except Exception as exc:
            print(f"Skip batch {batch_no}: {exc}")
            continue

        for yf_symbol in batch_symbols:
            try:
                df = _get_ticker_frame(data, yf_symbol)
                if df.empty or len(df) < 25:
                    continue

                close = pd.to_numeric(df["Close"], errors="coerce")
                high = pd.to_numeric(df["High"], errors="coerce")
                low = pd.to_numeric(df["Low"], errors="coerce")
                volume = pd.to_numeric(df["Volume"], errors="coerce")
                if close.isna().all() or volume.isna().all():
                    continue

                amount = close * volume
                amplitude = (high - low) / close.shift(1)
                atr_14 = _atr(high, low, close, window=14)

                avg_volume_20 = volume.rolling(window=20).mean().iloc[-1]
                avg_volume_lots_20 = avg_volume_20 / 1000
                avg_amount_20 = amount.rolling(window=20).mean().iloc[-1]
                avg_amplitude_20 = amplitude.rolling(window=20).mean().iloc[-1]
                current_price = close.iloc[-1]

                if avg_volume_lots_20 < MIN_AVG_VOLUME_LOTS:
                    continue
                if avg_amount_20 < MIN_AVG_AMOUNT:
                    continue
                if avg_amplitude_20 < MIN_AVG_AMPLITUDE:
                    continue
                if current_price < MIN_PRICE or current_price > MAX_PRICE:
                    continue

                ret_5 = (close.iloc[-1] / close.iloc[-6]) - 1
                ret_20 = (close.iloc[-1] / close.iloc[-21]) - 1
                vol_ratio = volume.iloc[-1] / avg_volume_20 if avg_volume_20 else np.nan

                symbol = symbol_map[yf_symbol]["symbol"]
                chip_values = {col: 0 for col in CHIP_COLUMNS}
                if not chip_by_symbol.empty and symbol in chip_by_symbol.index:
                    chip_values.update(chip_by_symbol.loc[symbol, CHIP_COLUMNS].to_dict())

                results.append(
                    {
                        "symbol": symbol,
                        "name": symbol_map[yf_symbol]["name"],
                        "price": current_price,
                        "avg_vol": avg_volume_lots_20,
                        "avg_amt": avg_amount_20,
                        "avg_amp": avg_amplitude_20,
                        "atr_14": atr_14.iloc[-1],
                        "ret_5": ret_5,
                        "ret_20": ret_20,
                        "vol_ratio": vol_ratio,
                        **chip_values,
                    }
                )
            except Exception as exc:
                print(f"Skip {yf_symbol}: {exc}")
                continue

    return pd.DataFrame(results)


def z_score(series):
    values = pd.to_numeric(series, errors="coerce").fillna(0)
    std = values.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(0, index=values.index)
    return (values - values.mean()) / std


def add_reason(row):
    reason_map = {
        "avg_amp_z": "20日平均振幅高",
        "atr_14_z": "ATR波動度高",
        "avg_vol_z": "20日均量充足",
        "avg_amt_z": "成交金額大",
        "vol_ratio_z": "量能明顯放大",
        "ret_5_z": "近5日動能強",
        "ret_20_z": "近20日趨勢佳",
        "main_buy_5d_z": "主力近5日偏買",
        "foreign_buy_5d_z": "外資近5日偏買",
        "investment_trust_buy_5d_z": "投信近5日偏買",
        "margin_change_pct_z": "融資動能升溫",
        "short_change_pct_inverse_z": "融券壓力下降",
    }
    ranked = sorted(reason_map, key=lambda col: row.get(col, 0), reverse=True)
    positive = [reason_map[col] for col in ranked if row.get(col, 0) > 0]
    return "、".join(positive[:3]) if positive else "綜合條件相對均衡"


def score_and_rank(df):
    if df.empty:
        return df

    df = df.copy()
    raw_factors = [
        "avg_amp",
        "atr_14",
        "avg_vol",
        "avg_amt",
        "vol_ratio",
        "ret_5",
        "ret_20",
        *CHIP_COLUMNS,
    ]
    for factor in raw_factors:
        if factor not in df.columns:
            df[factor] = 0
        df[f"{factor}_z"] = z_score(df[factor])

    df["short_change_pct_inverse_z"] = -df["short_change_pct_z"]
    df["volatility_factor"] = df[["avg_amp_z", "atr_14_z"]].mean(axis=1)
    df["liquidity_factor"] = df[["avg_vol_z", "avg_amt_z", "vol_ratio_z"]].mean(axis=1)
    df["momentum_factor"] = df[["ret_5_z", "ret_20_z"]].mean(axis=1)
    df["chip_factor"] = df[
        [
            "main_buy_5d_z",
            "foreign_buy_5d_z",
            "investment_trust_buy_5d_z",
            "margin_change_pct_z",
            "short_change_pct_inverse_z",
        ]
    ].mean(axis=1)

    df["total_score"] = (
        df["volatility_factor"] * 0.30
        + df["liquidity_factor"] * 0.25
        + df["momentum_factor"] * 0.25
        + df["chip_factor"] * 0.20
    )
    df["reason"] = df.apply(add_reason, axis=1)

    return df.sort_values(by="total_score", ascending=False).reset_index(drop=True)


def market_strength_summary(df_ranked):
    if df_ranked.empty:
        return "市場強弱：今日無符合條件候選股，盤面當沖條件偏弱。"

    avg_momentum = df_ranked[["ret_5", "ret_20"]].mean().mean()
    positive_ratio = (df_ranked["ret_5"] > 0).mean()
    if avg_momentum > 0.03 and positive_ratio >= 0.6:
        label = "偏強"
    elif avg_momentum < -0.02 or positive_ratio < 0.4:
        label = "偏弱"
    else:
        label = "中性震盪"

    return f"市場強弱：{label}，候選股5日動能為正比例 {positive_ratio:.0%}。"
