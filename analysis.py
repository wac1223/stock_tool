import pandas as pd
import yfinance as yf


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

def calculate_cross(close_prices):

    ma5 = close_prices.rolling(5).mean()

    ma25 = close_prices.rolling(25).mean()

    # 前日
    prev_ma5 = ma5.iloc[-2]
    prev_ma25 = ma25.iloc[-2]

    # 今日
    now_ma5 = ma5.iloc[-1]
    now_ma25 = ma25.iloc[-1]

    # ゴールデンクロス
    if prev_ma5 <= prev_ma25 and now_ma5 > now_ma25:
        return "GC"

    # デッドクロス
    elif prev_ma5 >= prev_ma25 and now_ma5 < now_ma25:
        return "DC"

    return "-"

def calculate_bollinger(close_prices):

    ma25 = close_prices.rolling(25).mean()

    std = close_prices.rolling(25).std()

    upper2 = ma25 + std * 2
    lower2 = ma25 - std * 2

    price = close_prices.iloc[-1]

    if price >= upper2.iloc[-1]:
        return "+25"

    elif price <= lower2.iloc[-1]:
        return "-25"

    elif price >= ma25.iloc[-1]:
        return "+15"

    else:
        return "-15"
    
def calculate_kairi25(close_prices):

    close_price = close_prices.iloc[-1]
    ma25 = close_prices.rolling(25).mean().iloc[-1]

    return round((close_price - ma25) / ma25 * 100, 2)


def calculate_volume_ratio(data):

    volume = data["Volume"].iloc[-1]
    volume5 = data["Volume"].rolling(5).mean().iloc[-1]

    return round(volume / volume5, 2)


def analyze_stock(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="2y")

    if data is None or data.empty:
        print(f"[SKIP] {symbol} データなし")
        return None

    close_prices = data["Close"].dropna()

    # 終値が2つ未満なら終了
    if len(close_prices) < 2:
        return None

    close_price = float(close_prices.iloc[-1])
    previous_close = float(close_prices.iloc[-2])

    change = close_price - previous_close
    change_percent = change / previous_close * 100

    volume = int(data["Volume"].iloc[-1])

    rsi = calculate_rsi(close_prices)
   
   
    kairi25 = calculate_kairi25(close_prices)
    volume_ratio = calculate_volume_ratio(data)

    macd, signal = calculate_macd(close_prices)
    cross = calculate_cross(close_prices)
    bollinger = calculate_bollinger(close_prices)

    # 75日移動平均
    ma75 = close_prices.rolling(window=75).mean().iloc[-1]
    ma75 = round(float(ma75), 2) if not pd.isna(ma75) else None

    # 200日移動平均
    ma200 = close_prices.rolling(window=200).mean().iloc[-1]
    ma200 = round(float(ma200), 2) if not pd.isna(ma200) else None

    # トレンド判定
    if ma75 is None or ma200 is None:
        trend = "判定不可"
    elif close_prices.iloc[-1] > ma75 > ma200:
        trend = "🟢 強い上昇"
    elif close_prices.iloc[-1] > ma75:
        trend = "🟢 上昇"
    elif close_prices.iloc[-1] > ma200:
        trend = "🟡 反発中"
    else:
        trend = "🔴 下降"

    return {
        "symbol": symbol,
        "現在価格": round(close_price, 2),
        "前日終値": round(previous_close, 2),
        "前日差額": round(change, 2),
        "前日比(%)": round(change_percent, 2),
        "出来高": volume,

        "RSI": rsi,
        "25日乖離率": kairi25,
        "出来高倍率": volume_ratio,

        "MACD": macd,
        "Signal": signal,
        "GC/DC": cross,
        "ボリンジャー": bollinger,

        "75日線": ma75,
        "200日線": ma200,
        "トレンド": trend,
    }












