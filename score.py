def calculate_score(rsi, kairi25, volume_ratio):
    score = 50
    reasons = []

    # RSI
    if 50 <= rsi <= 70:
        score += 20
        reasons.append("RSI良好")
    elif rsi > 70:
        score += 10
        reasons.append("買われすぎ")
    elif rsi < 30:
        score += 15
        reasons.append("売られすぎ")
    else:
        score -= 10

    # 25日乖離率
    if 0 <= kairi25 <= 10:
        score += 15
        reasons.append("25日線より上")
    elif kairi25 > 10:
        score += 5
        reasons.append("上昇しすぎ")
    elif kairi25 < -10:
        score -= 10
        reasons.append("25日線より大きく下")

    # 出来高倍率
    if volume_ratio >= 2:
        score += 20
        reasons.append("出来高急増")
    elif volume_ratio >= 1.5:
        score += 10
        reasons.append("出来高増加")

    # 0～100点
    score = max(0, min(score, 100))
    # ランク判定
    if score >= 90:
        rank = "S"
    elif score >= 80:
        rank = "A"
    elif score >= 65:
        rank = "B"
    elif score >= 50:
        rank = "C"
    elif score >= 30:
        rank = "D"
    else:
        rank = "E"

    # 星の数を判定
    if score >= 90:
        stars = "★★★★★"
    elif score >= 80:
        stars = "★★★★☆"
    elif score >= 65:
        stars = "★★★☆☆"
    elif score >= 50:
        stars = "★★☆☆☆"
    else:
        stars = "★☆☆☆☆"

    return score, rank, stars, reasons