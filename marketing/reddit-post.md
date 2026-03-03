# Reddit Post — TradeMemory Protocol

## Post Info

- **Subreddit:** r/algotrading (primary), r/metatrader5 (secondary)
- **Title:** I built an open-source memory layer for AI trading agents — it remembers what works across sessions
- **Flair:** Strategy / Infrastructure (depends on subreddit)

---

## Post Content

**TL;DR:** AI agents forget everything between sessions. I built a memory layer (MCP server) that records trades from MT5, discovers patterns, and generates strategy adjustments. Open source, MIT license, runs locally.

---

I've been running 4 XAUUSD strategies on MT5 (VolBreakout, PullbackEntry, IntradayMomentum, MeanReversion) and using Claude to analyze my trades. The problem: every new session starts from zero. The AI has no memory of what worked yesterday.

So I built TradeMemory — a 3-layer memory system that sits between MT5 and your AI agent:

**L1 (Raw Trades):** `mt5_sync.py` polls MT5 every 60 seconds, stores closed positions with full metadata — symbol, lots, SL/TP, session, strategy, hold duration, exit reason. No manual journaling.

**L2 (Pattern Discovery):** Reflection engine runs on your trade history and finds statistical patterns. Not "I think London is good" — it's "London session: 14W/0L, 100% WR over 14 trades" vs "Asian session: 1W/9L, 10% WR."

**L3 (Strategy Adjustments):** Converts L2 patterns into concrete parameter changes. Example output:

```
Parameter                │ Old  │ New   │ Reason
london_max_lot           │ 0.05 │ 0.08  │ London WR 100% — earned more room
asian_max_lot            │ 0.05 │ 0.025 │ Asian WR 10% — reduce exposure
min_confidence_threshold │ 0.40 │ 0.55  │ Trades below 0.55 have 0% WR
```

**What makes this different from FX Blue / MyFXBook / journaling apps:**

Those are dashboards for humans. TradeMemory is a memory layer for AI agents. Your agent loads L2/L3 data at session start, knows what worked, and doesn't repeat mistakes. It uses MCP (Model Context Protocol), so it plugs into Claude Desktop, Claude Code, Cursor, or any MCP client.

**My setup:**

- 4 EAs on XAUUSD, Demo @ FXTM (~$11K balance)
- mt5_sync.py running 24/7 with auto-reconnect + watchdog
- Daily reflection at 23:55 UTC
- 181 tests passing
- Last notable trade: VB BUY +$1,175 (03/02)

**97 parameter combinations backtested** (10,169 trades, 2024.01–2026.02):

| Strategy | Win Rate (of variants) | Avg PnL | Best Variant |
|---|---|---|---|
| IntradayMomentum | 94% (34/36) | +47.0% | +166.3% |
| PullbackEntry | 100% (9/9) | +40.9% | +69.5% |
| VolBreakout | 100% (16/16) | +29.2% | +51.9% |
| MeanReversion | 8% (3/36) | -13.7% | +16.0% |

All this backtest data flows through TradeMemory's L1→L2→L3 pipeline.

**Quick start:**

```bash
pip install tradememory-protocol
```

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "tradememory": {
      "command": "uvx",
      "args": ["tradememory-protocol"]
    }
  }
}
```

Then ask your AI: "Show my trading performance this week" or "Run a reflection on my last 20 trades."

**Links:**

- GitHub: https://github.com/mnemox-ai/tradememory-protocol (34 stars, MIT)
- PyPI: `pip install tradememory-protocol`
- Landing page: https://mnemox.ai/tradememory
- Demo: `python demo.py` — 30 simulated trades through the full pipeline, no API key needed

Happy to answer technical questions. This is a real tool I use daily, not a whitepaper.

— Sean (Mnemox AI)

---

## r/metatrader5 Variant

**Title:** Open-source tool that gives your MT5 EA an AI memory layer — auto-syncs trades, discovers patterns, adjusts parameters

**Body:** Same as above but replace the opening with:

If you're running EAs on MT5 and want your AI assistant to remember past trade results across sessions, I built an open-source memory layer called TradeMemory.

It syncs closed trades from MT5 every 60 seconds (via Python API), then runs pattern analysis and proposes parameter adjustments. Works with Claude, GPT, or any MCP-compatible AI client.

(Rest of post identical)

---

## Posting Notes

- **Timing:** Weekday mornings EST (09:00–12:00) — r/algotrading peak activity
- **Tone:** Technical peer-to-peer. Reddit hates self-promotion that reads like marketing. Lead with the problem, show real data, share the code.
- **Rules check:** r/algotrading allows project posts if they include substance, not just links. Include the backtest table and code snippet inline.
- **Avoid:** "Revolutionary," "game-changing," emojis, exclamation marks. Keep it dry and data-driven.
- **First comment:** Post a top-level reply with the architecture diagram (L1→L2→L3) and link to the demo output.
- **Engagement:** Answer every comment. r/algotrading respects builders who stick around.
- **Cross-post:** Wait 24h before posting to r/metatrader5 to avoid spam flags.
