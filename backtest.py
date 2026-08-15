"""現在のスコアロジックを過去株価で検証するための仮想売買ツール。

例:
    python backtest.py --symbols 7203 6758 8306 --start 2024-01-01

売買ルールはコマンドライン引数で明示する。終値で判定したシグナルは翌営業日の
始値で約定させるため、未来の価格を使う「先読み」は行わない。
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf

from analysis import (
    calculate_bollinger,
    calculate_cross,
    calculate_kairi25,
    calculate_macd,
    calculate_rsi,
    calculate_volume_ratio,
)
from score import calculate_score


OUTPUT_DIR = Path("backtest_output")


@dataclass
class Position:
    symbol: str
    shares: int
    entry_date: pd.Timestamp
    entry_price: float


def normalize_symbol(symbol: str) -> str:
    """国内4桁コードを yfinance 用のティッカーへ変換する。"""
    symbol = str(symbol).strip().upper()
    if (symbol.isdigit() and len(symbol) == 4) or (len(symbol) == 4 and symbol.endswith("A")):
        return f"{symbol}.T"
    return symbol


def score_at(data: pd.DataFrame, index: int) -> int | None:
    """index 日の終値までで、実運用と同じ calculate_score を実行する。"""
    window = data.iloc[: index + 1]
    close = window["Close"].dropna()
    if len(close) < 200:
        return None

    rsi = calculate_rsi(close)
    kairi25 = calculate_kairi25(close)
    volume_ratio = calculate_volume_ratio(window)
    macd, macd_signal = calculate_macd(close)
    cross = calculate_cross(close)
    bollinger = calculate_bollinger(close)
    ma75 = close.rolling(75).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1]
    price = close.iloc[-1]

    if price > ma75 > ma200:
        trend = "🟢 強い上昇"
    elif price > ma75:
        trend = "🟢 上昇"
    elif price > ma200:
        trend = "🟡 反発中"
    else:
        trend = "🔴 下降"

    score, _, _, _ = calculate_score(
        rsi, kairi25, volume_ratio, macd, macd_signal, cross, bollinger, trend
    )
    return score


def load_prices(symbols: list[str], start: str, end: str | None) -> dict[str, pd.DataFrame]:
    prices: dict[str, pd.DataFrame] = {}
    # 指標の200営業日分を確保するため、指定開始日の約15か月前から取得する。
    download_start = (pd.Timestamp(start) - pd.DateOffset(months=15)).strftime("%Y-%m-%d")
    for symbol in symbols:
        yf_symbol = normalize_symbol(symbol)
        data = yf.Ticker(yf_symbol).history(start=download_start, end=end, auto_adjust=False)
        if data is None or data.empty:
            print(f"[SKIP] {symbol}: 株価を取得できませんでした")
            continue
        prices[symbol] = data.dropna(subset=["Open", "Close"])
    return prices


def run_backtest(
    prices: dict[str, pd.DataFrame],
    start: str,
    initial_cash: float,
    max_positions: int,
    buy_score: int,
    sell_score: int,
    max_holding_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    start_date = pd.Timestamp(start).tz_localize(None)
    calendar = sorted(
        {
            timestamp.tz_localize(None)
            for frame in prices.values()
            for timestamp in frame.index
            if timestamp.tz_localize(None) >= start_date
        }
    )
    cash = initial_cash
    positions: dict[str, Position] = {}
    pending_orders: list[tuple[str, str, pd.Timestamp, str]] = []
    trades: list[dict] = []
    equity_rows: list[dict] = []

    for day in calendar:
        # 前営業日のシグナルを当日の始値で約定する。
        for action, symbol, signal_day, reason in pending_orders:
            frame = prices[symbol]
            matching = frame.loc[frame.index.tz_localize(None) == day]
            if matching.empty:
                continue
            open_price = float(matching.iloc[0]["Open"])
            if action == "BUY" and symbol not in positions and len(positions) < max_positions:
                budget = cash / max(1, max_positions - len(positions))
                shares = int(budget // open_price)
                if shares > 0:
                    cost = shares * open_price
                    cash -= cost
                    positions[symbol] = Position(symbol, shares, day, open_price)
                    trades.append({"date": day.date(), "symbol": symbol, "action": "BUY", "price": open_price, "shares": shares, "amount": cost, "reason": reason})
            elif action == "SELL" and symbol in positions:
                position = positions.pop(symbol)
                proceeds = position.shares * open_price
                cash += proceeds
                trades.append({"date": day.date(), "symbol": symbol, "action": "SELL", "price": open_price, "shares": position.shares, "amount": proceeds, "reason": reason, "entry_date": position.entry_date.date(), "entry_price": position.entry_price, "profit": proceeds - position.shares * position.entry_price, "return_pct": (open_price / position.entry_price - 1) * 100})
        pending_orders = []

        candidates: list[tuple[int, str]] = []
        for symbol, frame in prices.items():
            row_indexes = frame.index[frame.index.tz_localize(None) == day]
            if len(row_indexes) == 0:
                continue
            index = frame.index.get_loc(row_indexes[0])
            if isinstance(index, slice):
                continue
            score = score_at(frame, int(index))
            if score is None:
                continue
            if symbol in positions:
                age = (day - positions[symbol].entry_date).days
                if score < sell_score:
                    pending_orders.append(("SELL", symbol, day, f"score<{sell_score}"))
                elif age >= max_holding_days:
                    pending_orders.append(("SELL", symbol, day, f"holding_days>={max_holding_days}"))
            elif score >= buy_score:
                candidates.append((score, symbol))

        # 同日に候補が多い場合はスコアの高い順に、空き枠分だけ発注する。
        slots = max_positions - len(positions)
        for score, symbol in sorted(candidates, reverse=True)[:slots]:
            pending_orders.append(("BUY", symbol, day, f"score>={buy_score} ({score})"))

        market_value = 0.0
        for symbol, position in positions.items():
            frame = prices[symbol]
            available = frame.loc[frame.index.tz_localize(None) <= day, "Close"]
            if not available.empty:
                market_value += position.shares * float(available.iloc[-1])
        equity_rows.append({"date": day.date(), "cash": cash, "market_value": market_value, "equity": cash + market_value, "open_positions": len(positions)})

    equity = pd.DataFrame(equity_rows)
    trade_log = pd.DataFrame(trades)
    final_equity = float(equity.iloc[-1]["equity"]) if not equity.empty else initial_cash
    closed = trade_log[trade_log["action"] == "SELL"] if not trade_log.empty else pd.DataFrame()
    summary = {
        "initial_cash": initial_cash,
        "final_equity": round(final_equity, 2),
        "return_pct": round((final_equity / initial_cash - 1) * 100, 2),
        "closed_trades": int(len(closed)),
        "win_rate_pct": round(float((closed["profit"] > 0).mean() * 100), 2) if not closed.empty else None,
        "rules": {"buy_score_gte": buy_score, "sell_score_lt": sell_score, "max_holding_days": max_holding_days, "max_positions": max_positions},
    }
    return trade_log, equity, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="スコアに基づく仮想売買バックテスト")
    parser.add_argument("--symbols", nargs="+", required=True, help="例: 7203 6758 AAPL")
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--initial-cash", type=float, default=1_000_000)
    parser.add_argument("--max-positions", type=int, default=5)
    parser.add_argument("--buy-score", type=int, default=75)
    parser.add_argument("--sell-score", type=int, default=40)
    parser.add_argument("--max-holding-days", type=int, default=20)
    args = parser.parse_args()

    prices = load_prices(args.symbols, args.start, args.end)
    if not prices:
        raise SystemExit("有効な株価データがありません。銘柄コードを確認してください。")
    trades, equity, summary = run_backtest(
        prices, args.start, args.initial_cash, args.max_positions,
        args.buy_score, args.sell_score, args.max_holding_days,
    )
    OUTPUT_DIR.mkdir(exist_ok=True)
    trades.to_csv(OUTPUT_DIR / "trades.csv", index=False, encoding="utf-8-sig")
    equity.to_csv(OUTPUT_DIR / "equity.csv", index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"結果を {OUTPUT_DIR.resolve()} に保存しました。")


if __name__ == "__main__":
    main()
