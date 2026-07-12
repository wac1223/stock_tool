print("=== START ===")
import os
import json
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import gspread
from zoneinfo import ZoneInfo
from datetime import datetime
from google.oauth2.service_account import Credentials
from watchlist import analyze_watchlist
from sheets import spreadsheet
from analysis import analyze_stock
from score import calculate_score, get_signal
from ai_comment import make_ai_comment
from analysis import analyze_us_market

now = datetime.now(ZoneInfo("Asia/Tokyo"))

#本番環境
LINE_TOKEN = os.environ["LINE_TOKEN"]
USER_ID = os.environ["USER_ID"]

#ローカル環境
#LINE_TOKEN = os.getenv("LINE_TOKEN", "")
#USER_ID = os.getenv("USER_ID", "")


# =========================
# ログ
# =========================
print(f"[START] {now} 実行開始")

# =========================
# データ読み込み
# =========================
try:
    watchlist = pd.read_csv(
    "https://docs.google.com/spreadsheets/d/1QndFPPD7_-0iFRQe_37oALHeDlJz_kvfvzrZZ1rSlAU/export?format=csv"
    )
    
    print(watchlist.columns.tolist()) 

    portfolio = []

    for symbol in watchlist["銘柄"].unique():

        trades = watchlist[
        watchlist["銘柄"] == symbol
        ]

        buy_trades = trades[
        trades["売買"] == "買"
        ]

        buy_shares = buy_trades["株数"].sum()

        sell_shares = trades[
        trades["売買"] == "売"
        ]["株数"].sum()

        total_shares = buy_shares - sell_shares

        if total_shares <= 0:
            continue

        total_cost = (
        buy_trades["株数"]
        * buy_trades["単価"]
         ).sum()

        print("========")
        print(symbol)
        print("buy_shares:", buy_shares, type(buy_shares))
        print("total_cost:", total_cost, type(total_cost))

        avg_price = total_cost / buy_shares


        company_name = buy_trades.iloc[0]["会社名"]

        portfolio.append({
        "銘柄": symbol,
        "会社名": company_name,
        "株数": total_shares,
        "購入価格": avg_price
        })

    watchlist = pd.DataFrame(portfolio)

except Exception as e:
    print("スプレッドシート読み込み失敗:", e)
    exit()

result = []

# =========================
# 株価取得・計算
# =========================
for _, row in watchlist.iterrows():

    try:
        symbol = row["銘柄"]
        purchase_price = float(row["購入価格"])
        shares = float(row["株数"])
        company_name = row["会社名"]

        analysis = analyze_stock(symbol)

        if analysis is None:
            continue


        # データ取得
        rsi = analysis["RSI"]
        kairi25 = analysis["25日乖離率"]
        volume_ratio = analysis["出来高倍率"]
        macd = analysis["MACD"]
        macd_signal = analysis["Signal"]
        cross = analysis["GC/DC"]
        bollinger = analysis["ボリンジャー"]

        close_price = analysis["現在価格"]
        previous_close = analysis["前日終値"]
        change = analysis["前日差額"]
       
        change_percent = analysis["前日比(%)"]
        alert = ""

        if change_percent >= 5:
            alert = "🚀 急騰"

        elif change_percent <= -5:
            alert = "⚠️ 急落"
            
        ma75 = analysis["75日線"]
        ma200 = analysis["200日線"]
        trend = analysis["トレンド"]
        print(trend)

        # 判定
        score, rank, stars, reasons = calculate_score(
            rsi,
            kairi25,
            volume_ratio,
            macd,
            macd_signal,
            cross,
            bollinger,
            trend
        )

        comment = make_ai_comment(
            rsi,
            kairi25,
            volume_ratio,
            macd,
            macd_signal,
            cross,
            bollinger,
            trend
        )

        signal_text = get_signal(score)

#signal_text = get_signal(score)
#        score, rank, stars, reasons = calculate_score(
#            analysis["RSI"],
#            analysis["25日乖離率"],
#            analysis["出来高倍率"],
#            analysis["MACD"],
#            analysis["Signal"],
#            analysis["GC/DC"],
#            analysis["ボリンジャー"],
#            analysis["トレンド"]
#        )

        close_price = analysis["現在価格"]
        previous_close = analysis["前日終値"]
        change = analysis["前日差額"]
        change_percent = analysis["前日比(%)"]

        ma75 = analysis["75日線"]
        ma200 = analysis["200日線"]
        trend = analysis["トレンド"]

        comment = make_ai_comment(
            rsi,
            kairi25,
            volume_ratio,
            macd,
            macd_signal,
            cross,
            bollinger,
            trend
            
        )
        signal = get_signal(score)


        market_value = close_price * shares
        cost_value = purchase_price * shares
        profit = market_value - cost_value

        if cost_value > 0:
            profit_percent = profit / cost_value * 100
        else:
            profit_percent = 0
             
        result.append({
            "銘柄": symbol,
            "会社名": company_name,
            "株数": shares,
            "購入価格": round(purchase_price, 2),
            "現在価格": round(close_price, 2),
            "RSI": rsi,
            "25日乖離率": kairi25,
            "出来高倍率": volume_ratio,
            "MACD": macd,
            "Signal": macd_signal,
            "GC/DC": cross,
            "ボリンジャー": bollinger,

            "75日線": ma75,
            "200日線": ma200,
            "トレンド": trend,

            "売買シグナル": signal,
            "スコア": score,
            "ランク": rank,
            "星": stars,
            "AIコメント":comment,
            "アラート": alert,
            "判定理由": "、".join(reasons),

            "前日終値": round(previous_close, 2),
            "前日差額": round(change, 2),
            "前日比(%)": round(change_percent, 2),
            "評価額": round(market_value, 0),
            "取得額": round(cost_value, 0),
            "損益": round(profit, 0),
            "損益率(%)": round(profit_percent, 2),
        })

    except Exception as e:
        print(f"[WATCH ERROR] {symbol}: {e}")
        print("失敗銘柄", symbol)
        continue

# =========================
# 結果DataFrame
# =========================
result_df = pd.DataFrame(result)

worksheet = spreadsheet.worksheet("保有状況")
worksheet.clear()

print(result_df.columns)
print(result_df[["会社名", "75日線"]])

worksheet.update(
    [result_df.columns.tolist()]
    + result_df.values.tolist()
)
print("保有状況更新完了")

us_df = analyze_us_market()

us_ws = spreadsheet.worksheet("米国市場")

us_ws.clear()

us_ws.update(
    [us_df.columns.tolist()]
    + us_df.values.tolist()
)

if result_df.empty:
    print("有効データなし終了")
    exit()

# =========================
# 資産集計
# =========================

total_market_value = result_df["評価額"].sum()
total_cost_value = result_df["取得額"].sum()
total_profit = result_df["損益"].sum()

if total_cost_value > 0:
    total_profit_percent = round(
        total_profit / total_cost_value * 100,
        2
    )
else:
    total_profit_percent = 0

# =========================
# 資産推移シート更新
# =========================

history_ws = spreadsheet.worksheet("資産推移")

history_ws.append_row([
    now.strftime("%Y-%m-%d %H:%M"),
    int(total_market_value),
    int(total_cost_value),
    int(total_profit),
    float(total_profit_percent)
])
# =========================
# 資産履歴作成
# =========================

if total_cost_value > 0:
    total_profit_percent = round(
        total_profit / total_cost_value * 100,
        2
    )
else:
    total_profit_percent = 0

asset_today = pd.DataFrame([{
    "日時": now.strftime("%Y-%m-%d %H:%M"),
    "総評価額": total_market_value,
    "総取得額": total_cost_value,
    "総損益": total_profit,
    "総損益率": total_profit_percent
}])


# =========================
# 資産履歴読み込み
# =========================

if os.path.exists("asset_history_intraday.csv"):
    asset_history = pd.read_csv("asset_history_intraday.csv")
else:
    asset_history = pd.DataFrame(
        columns=[
            "日時",
            "総評価額",
            "総取得額",
            "総損益",
            "総損益率"
        ]
    )

asset_history = pd.concat(
    [asset_history, asset_today],
    ignore_index=True
)

asset_history.to_csv(
    "asset_history_intraday.csv",
    index=False
)

# =========================
# 日次履歴
# =========================

daily_today = pd.DataFrame([{
    "日付": now.strftime("%Y-%m-%d"),
    "総評価額": total_market_value,
    "総取得額": total_cost_value,
    "総損益": total_profit,
    "総損益率": total_profit_percent
}])

if os.path.exists("asset_history_daily.csv"):
    daily_history = pd.read_csv(
        "asset_history_daily.csv"
    )
else:
    daily_history = pd.DataFrame(
        columns=[
            "日付",
            "総評価額",
            "総取得額",
            "総損益",
            "総損益率"
        ]
    )

today = now.strftime("%Y-%m-%d")

if (
    len(daily_history) == 0
    or daily_history.iloc[-1]["日付"] != today
):
    daily_history = pd.concat(
        [daily_history, daily_today],
        ignore_index=True
    )

daily_history.to_csv(
    "asset_history_daily.csv",
    index=False
)

asset_history["日時"] = pd.to_datetime(asset_history["日時"])

asset_history["総評価額"] = pd.to_numeric(asset_history["総評価額"])
asset_history["総取得額"] = pd.to_numeric(asset_history["総取得額"])
asset_history["総損益"] = pd.to_numeric(asset_history["総損益"])

asset_history = asset_history.sort_values("日時")

print(asset_history.dtypes)
print(asset_history.tail())

# =========================
# グラフ① 資産推移
# =========================

plt.figure(figsize=(12,6))

plt.plot(
    asset_history["日時"],
    asset_history["総評価額"],
    linewidth=3,
    marker="o",
    label="Portfolio Value"
)

plt.plot(
    asset_history["日時"],
    asset_history["総取得額"],
    linewidth=2,
    linestyle="--",
    label="Cost Value"
)

plt.title("Portfolio Value History")

plt.legend()

plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("asset_value_graph.png")

plt.close()

# =========================
# グラフ② 日次推移
# =========================

daily_history["日付"] = pd.to_datetime(
    daily_history["日付"]
)

plt.figure(figsize=(12,6))

plt.plot(
    daily_history["日付"],
    daily_history["総評価額"],
    linewidth=3,
    marker="o",
    label="Portfolio Value"
)

plt.plot(
    daily_history["日付"],
    daily_history["総取得額"],
    linewidth=2,
    linestyle="--",
    label="Cost Value"
)

plt.title("Daily Portfolio History")

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.savefig("asset_daily_graph.png")

plt.close()

print("グラフ保存完了")



# =========================
# ポートフォリオ出力
# =========================
# 損益率順に並べ替え
result_df = result_df.sort_values(
    "損益率(%)",
    ascending=False
)

try:
    result_df.to_excel("portfolio.xlsx", index=False)
except Exception as e:
    print("portfolio保存失敗:", e)
    
# =========================
# 履歴作成
# =========================
history_df = result_df[["銘柄", "現在価格"]].copy()
history_df["日付"] = now.strftime("%Y-%m-%d")
history_df = history_df[["日付", "銘柄", "現在価格"]]

# =========================
# 履歴読み込み＆結合
# =========================
if os.path.exists("price_history.xlsx"):
    try:
        old_history = pd.read_excel("price_history.xlsx")
    except:
        old_history = pd.DataFrame(columns=["日付", "銘柄", "現在価格"])
else:
    old_history = pd.DataFrame(columns=["日付", "銘柄", "現在価格"])

history_df = pd.concat([old_history, history_df], ignore_index=True)

# =========================
# 履歴保存
# =========================
try:
    history_df.to_excel("price_history.xlsx", index=False)
except Exception as e:
    print("履歴保存失敗:", e)

# =========================
# サマリー
# =========================
total = len(result_df)
positive = len(result_df[result_df["損益率(%)"] > 0])
negative = len(result_df[result_df["損益率(%)"] < 0])
avg = round(result_df["損益率(%)"].mean(), 2)

best = result_df.loc[result_df["損益率(%)"].idxmax(), "銘柄"]
worst = result_df.loc[result_df["損益率(%)"].idxmin(), "銘柄"]

summary_df = pd.DataFrame({
    "項目": [
        "銘柄数",
        "総評価額",
        "総取得額",
        "総損益",
        "総損益率",
        "プラス",
        "マイナス",
        "最高",
        "最低"
    ],
    "値": [
        total,
        f"{total_market_value:,.0f}円",
        f"{total_cost_value:,.0f}円",
        f"{total_profit:,.0f}円",
        f"{total_profit_percent}%",
        positive,
        negative,
        best,
        worst
    ]
})

# =========================
# 監視銘柄状況
# =========================

watch_ws = spreadsheet.worksheet("監視銘柄")

watch_df = pd.DataFrame(
    watch_ws.get_all_records()
)
 
watch_message = "\n👀 監視銘柄\n\n"

for _, row in watch_df.iterrows():

    try:
        symbol = row["銘柄"]
        print("銘柄", symbol)

        stock = yf.Ticker(symbol)
        data = stock.history(period="2y")
        print("株価取得成功", symbol)
        if data is None or len(data) < 2:
            continue

        current_price = float(data["Close"].iloc[-1])
        year_data = data
        
        # 75日移動平均
        if len(data) >= 75:
            ma75 = round(data["Close"].rolling(window=75).mean().iloc[-1], 2)
        else:
            ma75 = ""
            
       
        high_52 = year_data["High"].max()
        low_52 = year_data["Low"].min()

        high_gap = (
            (current_price / high_52) - 1
        ) * 100

        low_gap = (
            (current_price / low_52) - 1
        ) * 100

        if len(year_data) >= 5:
            change_5d = (
            (current_price / year_data["Close"].iloc[-5]) - 1
        ) * 100
        else:
            change_5d = None
        
        previous_close = float(data["Close"].iloc[-2])

        change = current_price - previous_close
        change_pct = (
            change / previous_close * 100
        )

        watch_message += (
            f"📌 {row['会社名']}\n"
            f"終値: {current_price:.0f}円\n"
            f"前日比: {change:+.0f}円 "
            f"({change_pct:+.2f}%)\n"
        )

        if change_5d is not None:
            watch_message += (
                f"5日騰落率: {change_5d:+.2f}%\n"
            )

        watch_message += (
            f"52週高値まで: {high_gap:.1f}%\n"
            f"52週安値から: {low_gap:.1f}%\n\n"
        )

               
        watch_message += "\n"
        
    except Exception as e:
        print(f"[WATCH ERROR] {symbol}: {e}")
        continue
# =========================
# ダッシュボード出力
# =========================
try:
    with pd.ExcelWriter("dashboard.xlsx") as writer:
        summary_df.to_excel(writer, sheet_name="サマリー", index=False)
        result_df.to_excel(writer, sheet_name="保有状況", index=False)
        history_df.to_excel(writer, sheet_name="履歴", index=False)
        asset_history.to_excel(writer,sheet_name="資産推移",index=False)
        watch_df.to_excel(writer,sheet_name="監視銘柄",index=False)
except Exception as e:
    print("dashboard保存失敗:", e)

# =========================
# LINE通知
# =========================

try:

    ranking = result_df.sort_values(
    "損益率(%)",
    ascending=False
    )
    
    attention = result_df.sort_values(
        ["スコア", "前日比(%)"],
        ascending=[False, False]
    ).iloc[0]
    change_amount = 0
    change_percent = 0

    if len(asset_history) >= 2:

        previous_value = asset_history.iloc[-2]["総評価額"]

        change_amount = (
        total_market_value - previous_value
        )

        if previous_value > 0:

         change_percent = round(
            change_amount / previous_value * 100,
            2
        )    
        if change_amount > 0:

            change_text = (
            f"🟢📈 +{change_amount:,.0f}円\n"
            f"(+{change_percent:.2f}%)"
        )

        elif change_amount < 0:

            change_text = (
        f"🔴📉 {change_amount:,.0f}円\n"
        f"({change_percent:.2f}%)"
        )

        else:

            change_text = (
        "⚪ 変化なし\n"
        "(0.00%)"
    )
            
    profit_icon = "🟢" if total_profit >= 0 else "🔴"
        
    message = (    

    "📊 今日の資産状況\n\n"
    f"総評価額: {total_market_value:,.0f}円\n"
    f"総損益: {total_profit:,.0f}円\n"
    f"総損益率: {total_profit_percent}%\n\n"
    f"📈 前回通知から\n"
    f"{change_amount:+,.0f}円\n"
    f"({change_percent:+.2f}%)\n\n"

    "🔥 今日の注目銘柄\n\n"
    f"{attention['会社名']}\n"
    f"現在価格: {attention['現在価格']}円\n"
    f"シグナル: {attention['売買シグナル']}\n"
    f"{attention['アラート']}\n"
    f"AI: {attention['AIコメント']}\n\n"
)

# =====================
# 上位3銘柄
# =====================

    top3 = ranking.head(3)

    message += "🏆 上位3銘柄\n\n"

    for i, (_, row) in enumerate(top3.iterrows(), start=1):

        message += (
            f"🟢 {i}位 {row['会社名']}\n"
            f"現在価格: {row['現在価格']}\n"
            f"前日比: {row['前日差額']}\n"
            f"損益: {row['損益']:,.0f}円\n"
            f"損益率: {row['損益率(%)']}%\n"
            f"評価: {row['星']}\n"
            f"強気スコア: {row['スコア']}点\n"
            f"AI: {row['AIコメント']}\n\n"
            f"シグナル: {row['売買シグナル']}\n\n"
            f"{attention['アラート']}\n"
        )

# =====================
# 下位3銘柄
# =====================

    bottom3 = ranking.tail(3)

    message += "⚠️ 下位3銘柄\n\n"
   

    for i, (_, row) in enumerate(
    bottom3.sort_values("損益率(%)").iterrows(),
    start=1
):

        message += (
        f"🔴 {i}位 {row['会社名']}\n"
        f"現在価格: {row['現在価格']}\n"
        f"前日比: {row['前日差額']} "
        f"損益: {row['損益']:,.0f}円\n"
        f"損益率: {row['損益率(%)']}%\n\n"
        f"評価: {row['星']}\n"
        f"強気スコア: {row['スコア']}点\n"
        f"AI: {row['AIコメント']}\n\n"
        f"シグナル: {row['売買シグナル']}\n\n"
    )
    
    
    print("===== TOP3 =====")
    print(top3)

    print("===== BOTTOM3 =====")
    print(bottom3)
#    for _, row in ranking.iterrows():
    message += watch_message
#     message += (
#        f"■ {row['会社名']}\n"
#        f"終値: {row['現在価格']}\n"
#        f"前日比: {row['前日差額']} "
#        f"({row['前日比(%)']}%)\n"
#        f"評価損益: {row['損益']:,.0f}円 "
#        f"({row['損益率(%)']}%)\n\n")
    sheet_url = "https://docs.google.com/spreadsheets/d/1QndFPPD7_-0iFRQe_37oALHeDlJz_kvfvzrZZ1rSlAU/edit"

    message += (
    "\n📊 詳細はこちら\n"
    f"{sheet_url}\n"
    )
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
       }

    payload = {
    "to": USER_ID,
    "messages": [
        {
            "type": "text",
            "text": message
        },
        {
            "type": "image",
            "originalContentUrl":
            "https://raw.githubusercontent.com/wac1223/stock_tool/main/asset_value_graph.png",
            "previewImageUrl":
            "https://raw.githubusercontent.com/wac1223/stock_tool/main/asset_value_graph.png"
        },
        {
            "type": "image",
            "originalContentUrl":
            "https://raw.githubusercontent.com/wac1223/stock_tool/main/asset_daily_graph.png",
            "previewImageUrl":
            "https://raw.githubusercontent.com/wac1223/stock_tool/main/asset_daily_graph.png"
        }
    ]
}

    r = requests.post(
        url,
        headers=headers,
        json=payload
    )
    print("LINE送信:", r.status_code)
    print(r.text)
except Exception as e:
    print("LINE送信失敗:", e)

# 監視銘柄分析
analyze_watchlist()


message += "\n🇺🇸 米国市場\n\n"

for _, row in us_df.iterrows():

    message += (
        f"{row['市場']}\n"
        f"{row['前日比％']:+.2f}%\n\n"
    )

    
print("銘柄数:", len(result_df))
print(result_df[["銘柄","評価額"]])
print(f"[END] 完了 銘柄数: {total}")
print("=== END ===")
