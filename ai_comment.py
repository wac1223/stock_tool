def make_ai_comment(
    rsi,
    kairi25,
    volume_ratio,
    macd,
    signal,
    cross,
    bollinger,
    trend
):
    """
    AIコメントを返す
    """

    comments = []

    # ==========================
    # トレンド
    # ==========================
    comments.append(trend)

    # ==========================
    # MACD
    # ==========================
    if macd > signal:
        comments.append("MACDは買いシグナルです。")
    else:
        comments.append("MACDは売りシグナルです。")

    # ==========================
    # GC / DC
    # ==========================
    if cross == "GC":
        comments.append("ゴールデンクロスが発生し、上昇トレンド入りの可能性があります。")

    elif cross == "DC":
        comments.append("デッドクロスが発生し、短期的な下落に注意が必要です。")

    # ==========================
    # RSI
    # ==========================
    if rsi >= 70:
        comments.append("買われ過ぎ水準です。")

    elif rsi <= 30:
        comments.append("売られ過ぎ水準です。")

    elif 45 <= rsi <= 60:
        comments.append("RSIは良好な水準です。")

    # ==========================
    # 25日乖離率
    # ==========================
    if kairi25 >= 10:
        comments.append("25日線から大きく上に乖離しています。")

    elif kairi25 <= -10:
        comments.append("25日線から大きく下に乖離しています。")

    # ==========================
    # 出来高
    # ==========================
    if volume_ratio >= 2:
        comments.append("出来高が急増しています。")

    elif volume_ratio >= 1.5:
        comments.append("出来高が増加しています。")

    # ==========================
    # ボリンジャーバンド
    # ==========================
    if bollinger == "-2S":
        comments.append("ボリンジャーバンド-2σ付近です。売られすぎから反発する可能性があります。")

    elif bollinger == "-1S":
        comments.append("ボリンジャーバンド-1σ付近です。やや弱含みですが、反発に注目です。")

    elif bollinger == "+1S":
        comments.append("ボリンジャーバンド+1σ付近です。上昇基調ですが、過熱感に注意しましょう。")

    elif bollinger == "+2S":
        comments.append("ボリンジャーバンド+2σ付近です。買われすぎの可能性があり、利益確定売りに注意です。")

    # ==========================
    # コメントが無い場合
    # ==========================
    if len(comments) == 0:
        return "大きな変化はありません。"

    # ==========================
    # AIレポート作成
    # ==========================
    report = "【AI分析レポート】\n\n"

    for c in comments:
        report += f"・{c}\n"

    report += "\n"

    if trend == "強い上昇":
        report += "📈 中長期的にも強い上昇トレンドが継続しています。\n"
        report += "押し目買い候補として注目です。"

    elif trend == "上昇":
        report += "👍 上昇トレンドを維持しています。\n"
        report += "順張りが有利な局面です。"

    elif trend == "下降":
        report += "⚠️ 下落トレンドです。\n"
        report += "無理な買いは避け、反転サインを待ちましょう。"

    else:
        report += "➡️ 方向感が乏しいため、様子見が無難です。"

    return report