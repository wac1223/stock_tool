import time
import pandas as pd
import yfinance as yf

from analysis import analyze_stock
from sheets import spreadsheet
from ai_comment import make_ai_comment
from score import calculate_score



def analyze_watchlist():

    print("===== 監視銘柄分析開始 =====")

    watch_sheet = spreadsheet.worksheet("監視銘柄")

    watch_df = pd.DataFrame(
        watch_sheet.get_all_records()
    )

    results = []

    for row_number, (_, row) in enumerate(watch_df.iterrows(), start=2):

        symbol = row["銘柄"]

        try:

            analysis = analyze_stock(symbol)

            if analysis is None:
                continue

            close = analysis["現在価格"]
            previous = analysis["前日終値"]
            change = analysis["前日差額"]
            change_percent = analysis["前日比(%)"]
            volume = analysis["出来高"]

            rsi = analysis["RSI"]
            kairi25 = analysis["25日乖離率"]
            volume_ratio = analysis["出来高倍率"]

            macd = analysis["MACD"]
            signal = analysis["Signal"]
            cross = analysis["GC/DC"]
            bollinger = analysis["ボリンジャー"]

            trend = analysis["トレンド"]

            
            score, rank, stars, reasons = calculate_score(
                rsi,
                kairi25,
                volume_ratio,
                macd,
                signal,
                cross,
                bollinger,
                trend
            )
            ai_comment = make_ai_comment(
                rsi,
                kairi25,
                volume_ratio,
                macd,
                signal,
                cross,
                bollinger,
                trend
            )
            


            results.append({
                "row": row_number,
                "銘柄": symbol,
                "現在値": round(close, 2),
                "前日比": round(change, 2),
                "前日比％": round(change_percent, 2),
                "出来高": volume,
                "RSI": rsi,
                "25日乖離率": kairi25,
                "出来高倍率": volume_ratio,
                "MACD": macd,
                "Signal": signal,
                "GC/DC": cross,
                "Bollinger": bollinger,
                "75日線": analysis["75日線"],
                "200日線": analysis["200日線"],
                "トレンド": trend,
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
                f" MACD:{macd:.2f}"
                f" Signal:{signal:.2f}"
                f" GC/DC:{cross}"
                f" Bollinger:{bollinger}"
                f" 75日線:{analysis['75日線']}"
                f" 200日線:{analysis['200日線']}"
                f" トレンド:{trend}"
                f" 強気スコア:{score}"
                f" ランク:{rank}"
                f" 評価:{stars}"
                f" 理由:{'・'.join(reasons)}"
                f" AIコメント:{ai_comment}"
            )

        except Exception as e:

            print(f"{symbol} エラー")
            print(e)

    result_df = pd.DataFrame(results)
# 分析結果をシートへ反映

    for i, result in enumerate(results, start=2):

        watch_sheet.update(
            range_name=f"E{result['row']}:V{result['row']}",
            values=[[
                result["現在値"],
                result["前日比"],
                result["前日比％"],
                result["出来高"],
                result["RSI"],
                result["25日乖離率"],
                result["出来高倍率"],
                result["MACD"],
                result["Signal"],
                result["GC/DC"],
                result["Bollinger"],
                result["75日線"],
                result["200日線"],
                result["トレンド"],
                result["強気スコア"],
                result["ランク"],
                result["評価"],
                result["AIコメント"]
            ]]
            )
        
# =========================
# スコア履歴保存
# =========================

    from datetime import datetime

    history_sheet = spreadsheet.worksheet("スコア履歴")

    today = datetime.now().strftime("%Y-%m-%d")

    rows = []

    for _, row in result_df.iterrows():

        rows.append([
            today,
            row["銘柄"],
            row["強気スコア"]
        ])

    history_sheet.append_rows(rows)

    print(result_df)

    print("===== 監視銘柄分析終了 =====")
