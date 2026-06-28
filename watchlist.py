import pandas as pd
import yfinance as yf

from sheets import spreadsheet

###現在地～出来高まで追加
def calculate_rsi(close_prices, period=14):

    delta = close_prices.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(rsi.iloc[-1], 2)


###RSI関数を追加
def calculate_rsi(close_prices, period=14):

    delta = close_prices.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi.iloc[-1]), 1)

###評価を追加###
def calculate_score(rsi, kairi25, change_percent, volume_ratio):

    score = 0

    if 40 <= rsi <= 65:
        score += 1

    if -3 <= kairi25 <= 5:
        score += 1

    if change_percent > 0:
        score += 1
    
    if volume_ratio >= 1.5:
        score += 1

    if score == 3:
        return "★★★★★"

    elif score == 2:
        return "★★★★☆"

    elif score == 1:
        return "★★★☆☆"

    else:
        return "★★☆☆☆"
    


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
            
            ma25 = round(float(data["Close"].rolling(25).mean().iloc[-1]), 2)

            kairi25 = round(
                (close - ma25) / ma25 * 100,
                2
            )

            avg_volume = int(
                data["Volume"].rolling(25).mean().iloc[-1]
            )

            volume_ratio = round(
                volume / avg_volume,
                2
            )

            score = calculate_score(
                rsi,
                kairi25,
                change_percent,
                volume_ratio
            )



            results.append({
                "銘柄": symbol,
                "現在値": round(close, 2),
                "前日比": round(change, 2),
                "前日比％": round(change_percent, 2),
                "出来高": volume,
                "RSI": rsi,
                "25日乖離率": kairi25,
                "出来高倍率": volume_ratio,
                "評価": score,
            })

            print(
                f"{symbol} "
                f"{close:.2f}円 "
                f"{change_percent:+.2f}% "
                f"出来高:{volume:,}"
                f"RSI:{rsi:.1f}"
                f" 25日乖離:{kairi25:+.2f}%"
                f" 評価:{score}"

            )

        except Exception as e:

            print(f"{symbol} エラー")
            print(e)

    result_df = pd.DataFrame(results)
# 分析結果をシートへ反映

    for i, result in enumerate(results, start=2):

        watch_sheet.update(
            range_name=f"E{i}:L{i}",
            values=[[
                result["現在値"],
                result["前日比"],
                result["前日比％"],
                result["出来高"],
                result["RSI"],
                result["25日乖離率"],
                result["出来高倍率"],
                result["評価"]
            ]]
            )
    print()
    print(result_df)

    print("===== 監視銘柄分析終了 =====")