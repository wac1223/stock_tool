print("=== START ===")
# analysis.py
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# --- 設定（必要に応じて編集） ---
# Google Sheets から補助データを取る場合は main 側で取得して渡すのが簡単
# 例: sheet_info = {"7203.T": {"TAM": 1e12, "lockup_days": 90}}
# analysis.py は sheet_info を引数で受け取る設計にしている

# --- ユーティリティ関数 ---
def safe_get_financials(ticker: yf.Ticker) -> Optional[pd.DataFrame]:
    try:
        fin = ticker.financials
        if fin is None or fin.empty:
            return None
        return fin
    except Exception:
        return None

def revenue_growth_rate(fin: pd.DataFrame) -> Optional[float]:
    # fin の行ラベルは英語（例: 'Total Revenue'）の場合があるため複数候補で探す
    candidates = ["Total Revenue", "Revenue", "Net Sales", "売上高"]
    for key in candidates:
        if key in fin.index:
            rev = fin.loc[key].astype(float)
            if len(rev) >= 2:
                # 最新年と前年の比較（%）
                try:
                    latest = rev.iloc[0]
                    prev = rev.iloc[1]
                    if prev == 0:
                        return None
                    return (latest - prev) / abs(prev) * 100.0
                except Exception:
                    return None
    return None

def gross_margin(fin: pd.DataFrame) -> Optional[float]:
    # 粗利率 = Gross Profit / Revenue
    gp_keys = ["Gross Profit", "GrossIncome", "売上総利益"]
    rev_keys = ["Total Revenue", "Revenue", "Net Sales", "売上高"]
    gp = None
    rev = None
    for k in gp_keys:
        if k in fin.index:
            gp = fin.loc[k].astype(float)
            break
    for k in rev_keys:
        if k in fin.index:
            rev = fin.loc[k].astype(float)
            break
    if gp is None or rev is None:
        return None
    try:
        return float(gp.iloc[0] / rev.iloc[0] * 100.0)
    except Exception:
        return None

def operating_margin_trend(fin: pd.DataFrame) -> Optional[float]:
    # 営業利益の増減（最新 - 前年）
    op_keys = ["Operating Income", "OperatingProfit", "営業利益"]
    rev_keys = ["Total Revenue", "Revenue", "Net Sales", "売上高"]
    op = None
    rev = None
    for k in op_keys:
        if k in fin.index:
            op = fin.loc[k].astype(float)
            break
    for k in rev_keys:
        if k in fin.index:
            rev = fin.loc[k].astype(float)
            break
    if op is None or rev is None:
        return None
    try:
        latest_op = op.iloc[0]
        prev_op = op.iloc[1] if len(op) >= 2 else None
        if prev_op is None:
            return None
        return float(latest_op - prev_op)
    except Exception:
        return None

def has_subscription_revenue(ticker: yf.Ticker) -> Optional[bool]:
    # 自動判定は難しいため、決算の "business summary" や "info" をヒントにする
    try:
        info = ticker.info
        desc = ""
        for k in ["longBusinessSummary", "businessSummary", "description"]:
            if k in info and info[k]:
                desc = info[k].lower()
                break
        if not desc:
            return None
        keywords = ["subscription", "saas", "recurring", "maintenance", "保守", "サブスク"]
        return any(kw in desc for kw in keywords)
    except Exception:
        return None

# --- スコアリングロジック ---
def score_from_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    # シンプルな重み付けスコア（必要に応じて調整）
    score = 0.0
    reasons = []

    # 売上成長率
    rg = metrics.get("revenue_growth")
    if rg is not None:
        if rg >= 30:
            score += 30; reasons.append("高い売上成長")
        elif rg >= 10:
            score += 15; reasons.append("適度な売上成長")
        else:
            score += 0; reasons.append("売上成長弱め")

    # 粗利率
    gm = metrics.get("gross_margin")
    if gm is not None:
        if gm >= 60:
            score += 25; reasons.append("高粗利")
        elif gm >= 40:
            score += 15; reasons.append("良好な粗利")
        else:
            score += 5; reasons.append("粗利低め")

    # 営業利益トレンド
    op_trend = metrics.get("op_margin_trend")
    if op_trend is not None:
        if op_trend > 0:
            score += 15; reasons.append("営業利益改善")
        else:
            score += 0; reasons.append("営業利益改善なし")

    # ストック収益
    sub = metrics.get("has_subscription")
    if sub is True:
        score += 15; reasons.append("ストック収益あり")
    elif sub is False:
        score += 0; reasons.append("ストック収益なし")

    # TAM（手動入力がある場合）
    tam = metrics.get("TAM")
    if tam is not None:
        if tam >= 1e12:
            score += 10; reasons.append("巨大市場")
        elif tam >= 1e11:
            score += 5; reasons.append("十分な市場")

    # ロックアップ（短いほどリスク）
    lockup = metrics.get("lockup_days")
    if lockup is not None:
        if lockup <= 90:
            score -= 10; reasons.append("短いロックアップ（売り圧リスク）")
        elif lockup <= 180:
            score -= 5; reasons.append("中程度のロックアップ")

    # 正規化
    final_score = max(0, min(100, score))
    return {"score": final_score, "raw_score": score, "reasons": reasons}

# --- メイン分析関数 ---
def analyze_stock(symbol: str, sheet_info: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    symbol: yfinance で使えるティッカー（例 "7203.T"）
    sheet_info: 補助データ辞書。例: {"7203.T": {"TAM": 1e12, "lockup_days": 90}}
    戻り値: 指標とスコアの辞書
    """
    ticker = yf.Ticker(symbol)
    fin = safe_get_financials(ticker)

    metrics = {
        "symbol": symbol,
        "revenue_growth": None,
        "gross_margin": None,
        "op_margin_trend": None,
        "has_subscription": None,
        "TAM": None,
        "lockup_days": None
    }

    if fin is not None:
        metrics["revenue_growth"] = revenue_growth_rate(fin)
        metrics["gross_margin"] = gross_margin(fin)
        metrics["op_margin_trend"] = operating_margin_trend(fin)

    metrics["has_subscription"] = has_subscription_revenue(ticker)

    # sheet_info から補助データを取得
    if sheet_info and symbol in sheet_info:
        info = sheet_info[symbol]
        metrics["TAM"] = info.get("TAM")
        metrics["lockup_days"] = info.get("lockup_days")

    # スコアリング
    score_result = score_from_metrics(metrics)
    metrics.update(score_result)
    return metrics

# --- テスト用実行 ---
if __name__ == "__main__":
    # 例: python analysis.py 7203.T
    import sys
    if len(sys.argv) >= 2:
        sym = sys.argv[1]
        print(analyze_stock(sym))
    else:
        print("Usage: python analysis.py <TICKER>")
