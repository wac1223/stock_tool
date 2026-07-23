def get_buy_add_signal(
    rsi,
    kairi25,
    bollinger,
    trend,
    cross
):
    """
    中長期保有前提の『買い足し検討シグナル』を返す
    """

    # まず中長期トレンドが崩れていないことが前提
    if trend not in ["🟢 強い上昇", "🟢 上昇", "🟡 反発中"]:
        return "❌ 買い足し非推奨（トレンド弱い）"

    # 25日乖離率：押し目〜軽い下落を狙う
    if kairi25 > 0:
        # すでに25日線より上なら「押し目」ではない
        return "⚪ 様子見（押し目ではない）"

    # RSI：過熱は避ける
    if rsi > 70:
        return "⚪ 様子見（RSI過熱気味）"

    # ボリンジャー：-1σ〜-2σは押し目〜売られすぎ
    if bollinger in ["-1S", "-2S", "中心"]:
        # DCでも中長期なら『調整中の押し目』とみなす
        if cross == "DC":
            return "🟡 調整中押し目（段階的買い足し検討）"
        else:
            return "🟢 押し目買い候補（買い足し検討）"

    # それ以外は慎重に
    return "⚪ 様子見（条件弱い）"
