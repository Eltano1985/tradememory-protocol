"""
Trade Advisor — Event-driven memory recall + behavioral check.

NOT a scheduled report. Only speaks when it has something worth saying.

Called by mt5_sync.py when a new position is OPENED.
Queries TradeMemory for similar past trades and behavioral warnings.
Sends Discord alert only if there's a meaningful pattern to flag.

Design principle: silence is default, warning is exception.
"""

import os
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

load_dotenv()

TRADEMEMORY_API = os.getenv("TRADEMEMORY_API", "http://localhost:8000")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ---------------------------------------------------------------------------
# Thresholds — when to speak vs stay silent
# ---------------------------------------------------------------------------

# Minimum OWM score to consider a memory relevant
MIN_RECALL_SCORE = 0.2

# If past similar trades have avg PnL below this, warn
LOSS_PATTERN_THRESHOLD = -50.0

# Minimum number of similar trades to make a judgment
MIN_SIMILAR_TRADES = 2


def send_discord_alert(message: str, color: int = 0xE74C3C):
    """Send Discord alert. Only for warnings — not routine notifications."""
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        payload = {
            "embeds": [{
                "title": "TradeMemory — Advisor",
                "description": message,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }]
        }
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception:
        pass


def recall_similar(symbol: str, strategy: str, session: str) -> List[Dict]:
    """Query OWM for similar past trades."""
    try:
        resp = requests.post(
            f"{TRADEMEMORY_API}/owm/recall",
            json={
                "symbol": symbol,
                "market_context": f"{symbol} {strategy} entry during {session} session.",
                "limit": 10,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("memories", [])
    except Exception:
        pass
    return []


def get_behavioral() -> Optional[Dict]:
    """Get behavioral analysis."""
    try:
        resp = requests.get(f"{TRADEMEMORY_API}/owm/behavioral", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def get_agent_state() -> Optional[Dict]:
    """Get current agent affective state."""
    try:
        resp = requests.get(f"{TRADEMEMORY_API}/owm/state", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def advise_on_open(
    symbol: str,
    direction: str,
    strategy: str,
    entry_price: float,
    lot_size: float,
    session: str,
    ticket: int,
) -> Optional[str]:
    """
    Main advisor logic. Called when a new position is opened.

    Returns warning message if there's something worth saying.
    Returns None if everything looks fine (stay silent).
    """
    warnings: List[str] = []

    # -----------------------------------------------------------------------
    # 1. Recall similar past trades
    # -----------------------------------------------------------------------
    memories = recall_similar(symbol, strategy, session)
    relevant = [m for m in memories if m.get("score", 0) >= MIN_RECALL_SCORE]

    if len(relevant) >= MIN_SIMILAR_TRADES:
        pnls = [m.get("pnl", 0) for m in relevant if m.get("pnl") is not None]
        if pnls:
            avg_pnl = sum(pnls) / len(pnls)
            win_count = sum(1 for p in pnls if p > 0)
            loss_count = sum(1 for p in pnls if p <= 0)
            win_rate = win_count / len(pnls) if pnls else 0

            if avg_pnl < LOSS_PATTERN_THRESHOLD:
                worst = min(pnls)
                warnings.append(
                    f"**Similar past trades averaged ${avg_pnl:+.0f}** "
                    f"({win_count}W/{loss_count}L, worst: ${worst:+.0f})"
                )

            if win_rate < 0.35 and len(pnls) >= 3:
                warnings.append(
                    f"Win rate in similar setups: **{win_rate:.0%}** ({len(pnls)} trades)"
                )

        # Check if any relevant memory has a useful reflection
        for m in relevant[:3]:
            reflection = m.get("reflection")
            if reflection and len(reflection) > 10:
                warnings.append(f"Past note: *\"{reflection[:120]}\"*")
                break  # Only show one reflection

    # -----------------------------------------------------------------------
    # 2. Check behavioral patterns
    # -----------------------------------------------------------------------
    behavioral = get_behavioral()
    if behavioral:
        # Revenge trading detection: new trade within 30 min of a loss
        disposition = behavioral.get("disposition_ratio")
        if disposition and isinstance(disposition, (int, float)) and disposition > 2.0:
            warnings.append(
                "**Disposition effect detected** — cutting winners too early, holding losers too long"
            )

    # -----------------------------------------------------------------------
    # 3. Check agent state (drawdown, streaks)
    # -----------------------------------------------------------------------
    state = get_agent_state()
    if state:
        action = state.get("recommended_action", "normal")
        consec_losses = state.get("consecutive_losses", 0)
        drawdown = state.get("drawdown_pct", 0)

        if action == "stop_trading":
            warnings.append(
                f"**Agent recommends STOP TRADING** "
                f"(drawdown: {drawdown:.1f}%, losses streak: {consec_losses})"
            )
        elif action == "reduce_size":
            warnings.append(
                f"**Consider reducing size** "
                f"(drawdown: {drawdown:.1f}%, losses streak: {consec_losses})"
            )
        elif consec_losses >= 3:
            warnings.append(
                f"**{consec_losses} consecutive losses** — are you revenge trading?"
            )

    # -----------------------------------------------------------------------
    # Decision: speak or stay silent
    # -----------------------------------------------------------------------
    if not warnings:
        return None  # Nothing to say. Stay silent.

    # Build message
    header = (
        f"**New position: {strategy} {symbol} {direction.upper()}**\n"
        f"Entry: {entry_price:.2f} | Lots: {lot_size} | {session.capitalize()} session\n"
        f"---\n"
    )

    body = "\n".join(f"- {w}" for w in warnings)

    return header + body
