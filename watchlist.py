import pandas as pd
import yfinance as yf

from sheets import spreadsheet

def calculate_rsi(close_prices, period=14):

    delta = close_prices.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(rsi.iloc[-1], 2)

def analyze_watchlist():

    print("===== 監視銘柄分析開始 =====")

    watch_sheet = spreadsheet.worksheet("監視銘柄")

    watch_df = pd.DataFrame(
        watch_sheet.get_all_records()
    )

    results = []

    for _, row in watch_df.iterrows():

        symbol = row["銘柄"]

        try:

            stock = yf.Ticker(symbol)

            data = stock.history(period="3mo")

            if data.empty:
                print(f"{symbol} データ取得失敗")
                continue

            close = float(data["Close"].iloc[-1])

            previous = float(data["Close"].iloc[-2])

            change = close - previous

            change_percent = change / previous * 100

            volume = int(data["Volume"].iloc[-1])
            rsi = calculate_rsi(data["Close"])

            results.append({
                "銘柄": symbol,
                "現在値": round(close, 2),
                "前日比": round(change, 2),
                "前日比％": round(change_percent, 2),
                "出来高": volume,
                "RSI": rsi
            })

            print(
                f"{symbol} "
                f"{close:.2f}円 "
                f"{change_percent:+.2f}% "
                f"出来高:{volume:,}"
                f"RSI:{rsi:.1f}"
            )

        except Exception as e:

            print(f"{symbol} エラー")
            print(e)

    result_df = pd.DataFrame(results)
# 分析結果をシートへ反映

    for i, result in enumerate(results, start=2):

        watch_sheet.update(
            range_name=f"E{i}:I{i}",
            values=[[
                result["現在値"],
                result["前日比"],
                result["前日比％"],
                result["出来高"],
                result["RSI"]
            ]]
            )
    print()
    print(result_df)

    print("===== 監視銘柄分析終了 =====")