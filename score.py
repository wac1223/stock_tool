def calculate_score(
    rsi,
    kairi25,
    volume_ratio,
    macd,
    signal,
    cross,
    bollinger,
    trend
):
    score = 50
    reasons = []

    # RSI
    if 50 <= rsi <= 65:
        score += 15
        reasons.append("RSI適正")

    elif 65 < rsi <= 75:
        score += 5
        reasons.append("RSIやや過熱")

    elif rsi > 75:
        score -= 10
        reasons.append("RSI過熱")

    elif rsi < 30:
        score += 10
        reasons.append("RSI売られすぎ")

    else:
        score -= 5


    # 25日乖離率
    if 0 <= kairi25 <= 10:
        score += 15
        reasons.append("25日線上")
    elif kairi25 > 10:
        score += 5
        reasons.append("上昇加速")
    
    elif -10 <= kairi25 < 0:
        score += 5
        reasons.append("押し目")

    elif kairi25 < -10:
        score -= 10
        reasons.append("25日線大幅割れ")    

    # 出来高倍率

    if volume_ratio >= 3:
        score += 20
        reasons.append("出来高急増")

    elif volume_ratio >= 2:
        score += 10
        reasons.append("出来高増加")

    elif volume_ratio >= 1.5:
        score += 5
        reasons.append("出来高微増")



# GC/DC
    if cross == "GC":
        score += 15
        reasons.append("ゴールデンクロス")

    elif cross == "DC":
        score -= 15
        reasons.append("デッドクロス")

# ボリンジャーバンド
    if bollinger == "-2S":
        score += 10
        reasons.append("-2σ")

    elif bollinger == "-1S":
        score += 5
        reasons.append("-1σ")

    elif bollinger == "+1S":
        reasons.append("+1σ")

    elif bollinger == "+2S":
        score -= 10
        reasons.append("+2σ")
    
    # MACD
    if macd > signal:
        score += 10
        reasons.append("MACD買い")

    elif macd < signal:
        score -= 10
        reasons.append("MACD売り")
        

   # トレンド
    if trend == "🟢 強い上昇":
        score += 25
        reasons.append("長期上昇")

    elif trend == "🟢 上昇":
        score += 15
        reasons.append("上昇トレンド")

    elif trend == "🟡 反発中":
        score += 5
        reasons.append("反発局面")

    else:
        score -= 30
        reasons.append("下降トレンド")

    # 下降トレンドの上限
    if score > 75:
        score = 75
        
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

def get_signal(score):

    if score >= 90:
        return "🟢 強い買い"

    elif score >= 75:
        return "🟡 買い"

    elif score >= 55:
        return "⚪ 様子見"

    elif score >= 40:
        return "🟠 利益確定検討"

    else:
        return "🔴 売り注意"