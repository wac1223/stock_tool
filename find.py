import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ====== 設定 ======
LOCAL_CSV = r"C:\Users\MyPC\Documents\GitHub\stock_tool\data_j.csv"
LOOKBACK_DAYS = 90

VOLUME_MULTIPLIER = 1.5
VOLATILITY_MULTIPLIER = 1.8
# ==================


# ① JPX銘柄リストを読む（なみが保存したCSV）
def get_jpx_list():
    df = pd.read_csv(LOCAL_CSV, encoding="utf-8-sig")
    df = df[["コード", "銘柄名"]]
    df["ticker"] = df["コード"].astype(str).str.zfill(4) + ".T"
    return df


# ② 1銘柄の株価データ取得
def fetch_price(ticker):
    try:
        df = yf.download(ticker, period="3mo")
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"[ERROR] {ticker}: {e}")
        return None


# ③ 異常値シグナルを計算
def add_signals(df):
    df["vol_ma20"] = df["Volume"].rolling(20).mean()
    df["vol_signal"] = df["Volume"] > df["vol_ma20"] * VOLUME_MULTIPLIER

    df["ma25"] = df["Close"].rolling(25).mean()
    df["cross_signal"] = (df["Close"] > df["ma25"]) & (df["Close"].shift(1) <= df["ma25"].shift(1))

    df["range"] = df["High"] - df["Low"]
    df["range_ma20"] = df["range"].rolling(20).mean()
    df["volatility_signal"] = df["range"] > df["range_ma20"] * VOLATILITY_MULTIPLIER

    df["score"] = (
        df["vol_signal"].astype(int)
        + df["cross_signal"].astype(int)
        + df["volatility_signal"].astype(int)
    )

    return df


# ④ 1銘柄の最新シグナルを返す
def analyze_ticker(ticker, name):
    df = fetch_price(ticker)
    if df is None:
        return None

    df = add_signals(df)
    latest = df.iloc[-1]

    if latest["score"] == 0:
        return None

    return {
        "コード": ticker,
        "銘柄名": name,
        "終値": round(float(latest["Close"]), 2),
        "出来高": int(latest["Volume"]),
        "出来高↑": bool(latest["vol_signal"]),
        "25日線↑": bool(latest["cross_signal"]),
        "ボラ↑": bool(latest["volatility_signal"]),
        "スコア": int(latest["score"]),
    }


# ⑤ 全銘柄に対して実行
def main():
    jpx = get_jpx_list()
    results = []

    for _, row in jpx.iterrows():
        ticker = row["ticker"]
        name = row["銘柄名"]

        print(f"[CHECK] {ticker} {name}")
        r = analyze_ticker(ticker, name)
        if r:
            results.append(r)

    if not results:
        print("今日はシグナル銘柄なし")
        return

    df = pd.DataFrame(results).sort_values("スコア", ascending=False)
    print(df)

    df.to_csv("pre_bull_candidates.csv", index=False, encoding="utf-8-sig")
    print("\n→ pre_bull_candidates.csv に保存したで")


if __name__ == "__main__":
    main()
