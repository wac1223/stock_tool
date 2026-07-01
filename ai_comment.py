def make_ai_comment(
    rsi,
    kairi25,
    volume_ratio,
    macd,
    signal
):
    """
    AIコメントを返す
    """

    comments = []

    # ==========================
    # MACD
    # ==========================
    if macd > signal:
        comments.append("MACDは買いシグナルです。")
    else:
        comments.append("MACDは売りシグナルです。")

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
    # 総合コメント
    # ==========================
    if not comments:
        return "大きな変化はありません。引き続き監視しましょう。"

    return " ".join(comments)