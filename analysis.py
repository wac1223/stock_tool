import pandas as pd
import yfinance as yf
from datetime import datetime


# ==================== 決算日取得（analyze_stockより前に定義）====================

def get_earnings_date(symbol):
    """
    次回決算日と残り日数を取得。
    lxml が無くても、Yahooにデータがなくても落ちない。
    """
    try:
        stock = yf.Ticker(symbol)
        
        # --- 方法1: earnings_dates（lxmlが必要な場合あり）---
        try:
            df = stock.earnings_dates
            if df is not None and not df.empty:
                df.index = pd.to_datetime(df.index).tz_localize(None)
                today = pd.Timestamp.now().normalize()
                future = df[df.index >= today]
                if not future.empty:
                    earnings = future.index[0]
                    days = (earnings.date() - datetime.today().date()).days
                    return earnings.strftime("%Y/%m/%d"), f"あと{days}日"
        except Exception:
            pass  # lxml エラーなどは無視
        
        # --- 方法2: calendar（フォールバック）---
        try:
            cal = stock.calendar
            if isinstance(cal, dict):
                d = cal.get('Earnings Date')
                if isinstance(d, list) and d:
                    dt = pd.to_datetime(d[0]).tz_localize(None)
                    today = pd.Timestamp.now().normalize()
                    days = (dt.date() - datetime.today().date()).days
                    return dt.strftime("%Y/%m/%d"), f"あと{days}日"
        except Exception:
            pass
        
        # --- どっちも無理なら空欄 ---
        return "", ""
        
    except Exception as e:
        # 最後の保険：絶対に落ちない
        return "", ""


# ==================== テクニカル指標計算 ====================

def calculate_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1)


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
    prev_ma5 = ma5.iloc[-2]
    prev_ma25 = ma25.iloc[-2]
    now_ma5 = ma5.iloc[-1]
    now_ma25 = ma25.iloc[-1]

    if prev_ma5 <= prev_ma25 and now_ma5 > now_ma25:
        return "GC"
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
        return "+2S"
    elif price >= ma25.iloc[-1] + std.iloc[-1]:
        return "+1S"
    elif price <= lower2.iloc[-1]:
        return "-2S"
    elif price <= ma25.iloc[-1] - std.iloc[-1]:
        return "-1S"
    else:
        return "中心"


def calculate_kairi25(close_prices):
    close_price = close_prices.iloc[-1]
    ma25 = close_prices.rolling(25).mean().iloc[-1]
    return round((close_price - ma25) / ma25 * 100, 2)


def calculate_volume_ratio(data):
    volume = data["Volume"].iloc[-1]
    volume5 = data["Volume"].rolling(5).mean().iloc[-1]
    return round(volume / volume5, 2)


# ==================== メイン分析関数 ====================

def analyze_stock(symbol):
    yf_symbol = symbol

    # 日本株（4桁数字 または 末尾A）なら .T を付ける
    if (
        (symbol.isdigit() and len(symbol) == 4)
        or (len(symbol) == 4 and symbol.endswith("A"))
    ):
        yf_symbol += ".T"

    stock = yf.Ticker(yf_symbol)
    data = stock.history(period="2y")

    if data is None or data.empty:
        print(f"[SKIP] {symbol} データなし")
        return None

    close_prices = data["Close"].dropna()

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

    # ===== 決算情報取得 =====
    earnings_date, earnings_days = get_earnings_date(yf_symbol)
    print(f"{symbol} 決算日:{earnings_date} {earnings_days}")

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
        "決算日": earnings_date,
        "決算まで": earnings_days,
    }


# ==================== 米国市場分析 ====================

def analyze_us_market():
    us_list = {
        "NASDAQ": "^IXIC",
        "S&P500": "^GSPC",
        "SOX": "^SOX",
        "NVDA": "NVDA",
        "MSFT": "MSFT",
        "GOOGL": "GOOGL",
        "aapl": "aapl",
        "AMD": "AMD",
        "TSMC": "TSM",
        "SKHY": "SKHY",
        "PENG": "PENG"
    }

    results = []

    for name, ticker in us_list.items():
        stock = yf.Ticker(ticker)
        data = stock.history(period="5d")

        if len(data) < 2:
            continue

        current = float(data["Close"].iloc[-1])
        prev = float(data["Close"].iloc[-2])
        change = current - prev
        change_pct = change / prev * 100

        results.append({
            "市場": name,
            "現在値": round(current, 2),
            "前日比": round(change, 2),
            "前日比％": round(change_pct, 2)
        })

    return pd.DataFrame(results)