# MQL5.com Article / Forum Post — TradeMemory Protocol

## Post Info

- **Platform:** MQL5.com → Articles or Code Base (forum post fallback)
- **Title:** TradeMemory: An Open-Source Memory Layer for AI-Assisted Expert Advisors
- **Category:** Expert Advisors / Trading Systems
- **Language:** English

---

## Article Content

### TradeMemory: An Open-Source Memory Layer for AI-Assisted Expert Advisors

#### Introduction

Expert Advisors run statelessly. Each restart begins with no knowledge of past performance — which sessions were profitable, which strategies underperformed, or what parameter adjustments the data suggests. Traders compensate by manually reviewing backtests and optimization reports, but this workflow breaks down when AI agents enter the picture.

TradeMemory Protocol is an open-source system (MIT license) that adds persistent memory to AI-assisted EA workflows. It automatically syncs closed trades from MetaTrader 5, stores them in a structured database, runs pattern analysis, and generates strategy adjustment proposals — all accessible via MCP (Model Context Protocol) or REST API.

This article explains the architecture, shows integration with MT5, and presents validation data from 10,169 trades across 97 parameter combinations.

#### The Problem: Stateless AI Agents

Modern AI coding assistants (Claude, GPT, Cursor) can analyze trading data when you paste it into a chat window. But they cannot:

1. Remember yesterday's analysis in today's session
2. Automatically ingest new trades as they close
3. Track pattern evolution over weeks or months
4. Propose parameter changes based on accumulated evidence

TradeMemory solves all four.

#### Architecture: Three-Layer Memory

```
MT5 Terminal
    │
    ▼ (mt5_sync.py — polls every 60s)
┌─────────────────────────────────────────┐
│  TradeMemory Protocol Server            │
│                                         │
│  L1: Trade Journal (SQLite)             │
│      Raw trades with full metadata      │
│      Symbol, lots, SL/TP, session,      │
│      strategy, confidence, P&L          │
│                                         │
│  L2: Pattern Discovery (Reflection)     │
│      Win rate by session/strategy       │
│      Drawdown sequences                 │
│      Confidence correlation             │
│                                         │
│  L3: Strategy Adjustments               │
│      Lot sizing proposals               │
│      Session filters                    │
│      Confidence thresholds              │
│      Direction restrictions             │
└─────────────────────────────────────────┘
    │
    ▼ (MCP / REST API)
AI Agent (Claude Desktop, Claude Code, Cursor)
```

**L1** stores every closed position with fields that matter for analysis: magic number → strategy name mapping, session classification (Asia/London/NY), hold duration, and exit reasoning.

**L2** runs daily reflection at 23:55 UTC. It computes win rates by strategy, session, direction, and confidence level. It flags anomalies — a strategy that was profitable last month but has been losing for 2 weeks straight.

**L3** converts L2 findings into actionable proposals: "Increase london_max_lot from 0.05 to 0.08 because London WR = 100% over 14 trades." These are proposals, not automatic changes — the trader approves or rejects each one.

#### MT5 Integration

TradeMemory connects to MT5 via the official Python API (`MetaTrader5` package). No modifications to your EA code are required.

**mt5_sync.py** handles:
- Automatic connection with credentials from `.env` file
- Polling closed deals every 60 seconds
- Magic number → strategy name mapping (configurable per EA)
- Duplicate detection (INSERT OR IGNORE)
- Auto-reconnect with exponential backoff (60s → 600s)
- Watchdog script for process recovery

**Configuration example (.env):**
```
MT5_ACCOUNT=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
MT5_PATH=C:/Program Files/MetaTrader 5/terminal64.exe
```

**Prerequisites:**
- MetaTrader 5 with `Api=1` enabled in `common.ini` ([Experts] section)
- Python 3.12 (3.13+ not supported by MT5 package)
- `pip install MetaTrader5 python-dotenv requests`

#### Validation Data: 97 Parameter Combinations

To validate the system, I ran 97 strategy variants across 4 strategies on XAUUSD (1 Minute OHLC, H1 timeframe, 2024.01–2026.02). Total: 10,169 trades.

**Results summary:**

| Strategy | Variants | Profitable | Avg PnL | Best Variant | Best PnL |
|---|---|---|---|---|---|
| IntradayMomentum | 36 | 94% (34/36) | +47.0% | IM_XAUUSD_BUY_RR3.5_TH0.45 | +166.3% |
| PullbackEntry | 9 | 100% (9/9) | +40.9% | PB_XAUUSD_BUY_RR3_PCT0.5 | +69.5% |
| VolBreakout | 16 | 100% (16/16) | +29.2% | VB_XAUUSD_BUY_RR4_BUF0.1 | +51.9% |
| MeanReversion | 36 | 8% (3/36) | -13.7% | MR_XAUUSD_BUY_BB2_RSI30 | +16.0% |

**Key findings that L2 discovered:**
- BUY-only outperforms BOTH in all strategies during the 2024–2026 gold bull market (+100%)
- IntradayMomentum dominates with PF > 2.0 in top variants
- MeanReversion is viable only with BB ≥ 2.0 + RSI 30 + BUY-only (3 of 36 variants profitable)
- VolBreakout has consistent positive expectancy (16/16 profitable, avg realized RR = 1.37)

These findings are stored in L2 and accessible to the AI agent in every future session.

#### Querying Your Memory

Once connected, you ask your AI agent natural language questions:

- "How did my VolBreakout strategy perform this week?"
- "Which session has the worst win rate?"
- "Show me trades where confidence was below 0.5 — what happened?"
- "Run a reflection on my last 20 trades"

The agent reads L1/L2/L3 data via MCP tools and responds with context it retained from previous sessions.

**Available MCP tools:**
- `store_trade_memory` — Record a trade with full context
- `recall_similar_trades` — Find trades with similar market conditions
- `get_strategy_performance` — Aggregate stats per strategy
- `get_trade_reflection` — Deep analysis of a specific trade

**REST API** also available (30+ endpoints) for programmatic access or custom dashboard integration.

#### Installation

```bash
pip install tradememory-protocol
```

**Claude Desktop integration:**
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

**Run the demo (no API key needed):**
```bash
python demo.py
```

Runs 30 simulated XAUUSD trades through L1 → L2 → L3 pipeline. Output shows trade recording, pattern discovery, and strategy adjustment proposals.

#### Technical Specifications

- **Language:** Python 3.10+
- **MCP Server:** FastMCP 3.x (stdio transport)
- **REST API:** FastAPI + uvicorn
- **Storage:** SQLite (L3), JSON (L2)
- **Reflection:** Rule-based pattern analysis + optional Claude API for deeper insights
- **Tests:** 181 unit tests passing
- **License:** MIT

#### Conclusion

TradeMemory Protocol bridges the gap between stateless AI agents and the continuous learning that profitable trading demands. It does not replace your EA or your judgment — it gives your AI assistant the memory to build on yesterday's lessons instead of starting from zero.

The project is open source and actively developed. Contributions, bug reports, and feature requests are welcome.

**Links:**
- GitHub: https://github.com/mnemox-ai/tradememory-protocol
- PyPI: https://pypi.org/project/tradememory-protocol/
- Documentation: https://github.com/mnemox-ai/tradememory-protocol/tree/master/docs
- Landing Page: https://mnemox.ai/tradememory

---

## Forum Post Variant (Shorter)

If the article queue is too long, post in the MQL5 Trading Systems forum:

**Title:** TradeMemory — Open-Source AI Memory Layer for MT5 Expert Advisors

**Body:**

I built an open-source tool that adds persistent memory to AI-assisted EA workflows on MT5.

**What it does:**
- Auto-syncs closed trades from MT5 every 60 seconds (via Python API, no EA code changes)
- Stores full trade metadata in SQLite (strategy, session, confidence, P&L)
- Runs daily pattern analysis — finds which sessions/strategies/setups actually work
- Generates parameter adjustment proposals based on accumulated data
- AI agent loads this memory at session start — no more starting from zero

**Validated on:** 10,169 trades, 97 parameter combinations, 4 strategies on XAUUSD (2024.01–2026.02). IntradayMomentum avg +47%, VolBreakout 16/16 variants profitable.

**Tech:** Python, FastMCP, SQLite, MIT license. Works with Claude Desktop, Cursor, or any MCP client.

GitHub: https://github.com/mnemox-ai/tradememory-protocol
Install: `pip install tradememory-protocol`

Feedback welcome — especially from anyone running AI-assisted EAs.

— Sean (Mnemox AI)

---

## Posting Notes

- **MQL5 article review:** Takes 1–3 weeks. Submit via mql5.com/en/articles/new. Use `<pre class="code">` for code blocks in the editor.
- **Tone:** Formal-technical. MQL5 audience is experienced EA developers. They value precision, validation data, and reproducibility. No hype, no buzzwords.
- **Images required:** MQL5 articles typically need 3–5 figures. Prepare: (1) Architecture diagram, (2) L2 pattern output, (3) Backtest results table, (4) MT5 sync terminal screenshot, (5) Claude Desktop query screenshot.
- **Code samples:** MQL5 readers expect working code. The Python examples are fine since this is a Python tool, but mention explicitly that no MQL5 code changes are needed.
- **Avoid:** Marketing language, unsubstantiated claims, comparisons that dismiss MQL5's built-in tools. Respect the ecosystem.
- **Engagement:** MQL5 forum responses come slowly. Check weekly. Technical questions deserve detailed answers.
