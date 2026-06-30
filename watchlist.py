import pandas as pd
import yfinance as yf

from sheets import spreadsheet
from ai_comment import make_ai_comment
from score import calculate_score



###現在値～出来高まで追加
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


###MACD計算
def calculate_macd(close_prices):

    ema12 = close_prices.ewm(span=12, adjust=False).mean()

    ema26 = close_prices.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26

    signal = macd.ewm(span=9, adjust=False).mean()

    return (
        round(float(macd.iloc[-1]), 2),
        round(float(signal.iloc[-1]), 2)
    )


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
            macd, signal = calculate_macd(data["Close"])
            
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

            score, rank, stars, reasons = calculate_score(
                rsi,
                kairi25,
                volume_ratio,
                macd,
                signal
)
            ai_comment = make_ai_comment(
                rsi,
                kairi25,
                volume_ratio,
                macd,
                signal
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
                "強気スコア": score,
                "ランク": rank,
                "評価": stars,
                "理由": "・".join(reasons),
                "AIコメント": ai_comment,
            })

            print(
                f"銘柄{symbol} "
                f"現在値{close:.2f}円 "
                f"前日比{round(change, 2)} "
                f"前日比％{change_percent:+.2f}% "
                f" 出来高:{volume:,}"
                f" RSI:{rsi:.1f}"
                f" 25日乖離率:{kairi25:+.2f}%"
                f" 出来高倍率:{volume_ratio}"
                f" 強気スコア:{score}"
                f" ランク:{rank}"
                f" 評価:{stars}"
                f" 理由:(reasons)"
                f" AIコメント:{ai_comment}"
            )

        except Exception as e:

            print(f"{symbol} エラー")
            print(e)

    result_df = pd.DataFrame(results)
# 分析結果をシートへ反映

    for i, result in enumerate(results, start=2):

        watch_sheet.update(
            range_name=f"E{i}:M{i}",
            values=[[
                result["現在値"],
                result["前日比"],
                result["前日比％"],
                result["出来高"],
                result["RSI"],
                result["25日乖離率"],
                result["出来高倍率"],
                result["評価"],
                result["理由"]
            ]]
            )
    print()
    print(result_df)

    print("===== 監視銘柄分析終了 =====")