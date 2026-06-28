def make_ai_comment(rsi, kairi25, volume_ratio):
    # 強い上昇
    if rsi >= 70 and volume_ratio >= 2:
        return "出来高を伴って強く買われています。短期的には利益確定売りに注意。"

    # 上昇トレンド
    elif 50 <= rsi < 70 and kairi25 > 0:
        return "上昇トレンドが継続しています。押し目を待つ戦略も有効です。"

    # 売られすぎ
    elif rsi <= 30 and volume_ratio >= 1.5:
        return "売られすぎ水準です。反発候補として監視したい銘柄です。"

    # 下落トレンド
    elif rsi < 50 and kairi25 < 0:
        return "下降トレンドです。無理な買いは避けて様子を見ましょう。"

    # 出来高だけ増えている
    elif volume_ratio >= 2:
        return "出来高が急増しています。材料が出ている可能性があります。"

    # 25日線から大きく離れている
    elif kairi25 >= 10:
        return "25日移動平均線から大きく上に乖離しています。過熱感に注意。"

    elif kairi25 <= -10:
        return "25日移動平均線から大きく下に乖離しています。反発するか注目です。"

    # RSI良好
    elif 45 <= rsi <= 60:
        return "値動きは比較的安定しています。トレンドの継続を確認しましょう。"

    # それ以外
    return "大きな変化はありません。引き続き監視しましょう。"