# frontend.py
# Friendly Streamlit UI for the LangGraph stock assistant defined in backend.py
# Run with:  streamlit run frontend.py

import html
import json
import re
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command



import os

for key in ("sk-proj-9cC8l8dMoo0oFt7fvM5dWf3u_XA-UCvedSyvmQebIV45VkVgAqpIpep8PNrk7j28_-T3BlbkFJKCe-vHPdoXqPCnZ2ji3mBynMZsQowIPFuoQHaTyQjDgvjJd0SSqJUdVEqVjNiRumz22YNqlCcA", "C9PE94QUEW9VWGFM"):
    try:
        if key not in os.environ and key in st.secrets:
            os.environ[key] = st.secrets[key]
    except Exception:
        pass  # no secrets file locally; .env will be used instead

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY is missing. Add it in Settings > Secrets (or in your local .env file).")
    st.stop()

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="StockPilot Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Inline SVG icons (no emoji anywhere in the UI)
# ------------------------------------------------------------------
_ICON_PATHS = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/>'
            '<path d="M2 3h3l2.7 12.4a1 1 0 0 0 1 .8h9.6a1 1 0 0 0 1-.8L21 7H6"/>',
    "chart": '<path d="M3 17l6-6 4 4 8-9"/><path d="M15 6h6v6"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.5 7.2L4 20l1-4.5A8 8 0 1 1 21 12z"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
    "pause": '<rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/>',
    "up": '<path d="M12 19V5M5 12l7-7 7 7"/>',
    "down": '<path d="M12 5v14M19 12l-7 7-7-7"/>',
}


def icon(name: str, size: int = 20, color: str = "currentColor") -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{_ICON_PATHS[name]}</svg>'
    )


# ------------------------------------------------------------------
# Custom CSS
# ------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --bg: #fbf8f4;
    --card: #ffffff;
    --soft: #f3efe9;
    --border: #e8e2d9;
    --text: #1f2937;
    --muted: #6b7280;
    --brand: #0d9488;
    --brand-dark: #0f766e;
    --brand-soft: #e6f6f4;
    --blue-soft: #eef2ff;
    --green: #16a34a;
    --green-soft: #e8f7ee;
    --red: #dc2626;
    --red-soft: #fdecec;
    --amber: #d97706;
    --amber-soft: #fff6e5;
    --shadow: 0 6px 24px rgba(31, 41, 55, 0.07);
}

html, body, [class*="css"], .stApp, button, input, textarea {
    font-family: 'Nunito', sans-serif !important;
}

.stApp {
    background:
        radial-gradient(800px 420px at 90% -5%, rgba(13,148,136,0.10), transparent 60%),
        radial-gradient(700px 380px at -5% 5%, rgba(99,102,241,0.08), transparent 60%),
        var(--bg);
    color: var(--text);
}
.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
div[data-testid="stMarkdownContainer"] { color: var(--text); }

/* hide default chrome */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; padding-bottom: 6rem; max-width: 880px; }

/* ---------- icon helpers ---------- */
.ico-badge {
    width: 40px; height: 40px; border-radius: 12px; flex: none;
    display: inline-flex; align-items: center; justify-content: center;
}
.ico-teal  { background: var(--brand-soft); color: var(--brand-dark); }
.ico-blue  { background: var(--blue-soft);  color: #4f46e5; }
.ico-amber { background: var(--amber-soft); color: var(--amber); }
.ico-green { background: var(--green-soft); color: var(--green); }
.ico-red   { background: var(--red-soft);   color: var(--red); }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--card);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
    background: var(--soft);
    color: var(--text);
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 0.6rem 0.9rem;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all .15s ease;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--brand-soft);
    border-color: var(--brand);
    color: var(--brand-dark);
}
section[data-testid="stSidebar"] .stButton > button:disabled { opacity: .5; }

.side-label {
    font-size: 0.72rem; letter-spacing: .1em; text-transform: uppercase;
    color: var(--muted); margin: 1.4rem 0 .6rem 0; font-weight: 700;
}
.brand { display:flex; align-items:center; gap:.75rem; margin-bottom:.9rem; }
.brand-logo {
    width: 44px; height: 44px; border-radius: 14px; color: #fff;
    background: linear-gradient(135deg, #14b8a6, #0d9488);
    display:flex; align-items:center; justify-content:center;
    box-shadow: 0 6px 16px rgba(13,148,136,.28);
}
.brand-name { font-weight: 800; font-size: 1.15rem; letter-spacing: -.01em; }
.brand-sub { font-size: .78rem; color: var(--muted); }

.status-pill {
    display:inline-flex; align-items:center; gap:.5rem;
    padding: .4rem .9rem; border-radius: 999px; font-size: .82rem; font-weight: 700;
    background: var(--green-soft); color: var(--green);
}
.status-pill.wait { background: var(--amber-soft); color: var(--amber); }
.dot { width:8px; height:8px; border-radius:50%; background: currentColor; }
.status-pill.wait .dot { animation: pulse 1.3s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }

.meta-box {
    background: var(--soft); border-radius: 12px; padding: .7rem .9rem;
    font-size: .78rem; color: var(--muted); word-break: break-all;
}
.meta-box code { font-family: 'JetBrains Mono', monospace; color: var(--text); background: transparent; }

/* ---------- hero ---------- */
.hero { text-align:center; padding: 2.6rem 1rem 1rem; }
.hero .greet {
    display:inline-block; padding:.35rem .9rem; border-radius:999px; font-size:.82rem; font-weight:700;
    background: var(--brand-soft); color: var(--brand-dark); margin-bottom: 1rem;
}
.hero h1 {
    font-size: 2.5rem; font-weight: 800; letter-spacing: -.03em; margin: 0 0 .6rem;
    color: var(--text);
}
.hero h1 span { color: var(--brand); }
.hero p { color: var(--muted); font-size: 1.05rem; max-width: 520px; margin: 0 auto; line-height: 1.6; }
.feature-row { display:flex; gap:1rem; margin-top: 2.2rem; flex-wrap: wrap; }
.feature {
    flex: 1 1 230px; background: var(--card); border: 1px solid var(--border);
    border-radius: 20px; padding: 1.2rem; text-align: left; box-shadow: var(--shadow);
}
.feature h4 { margin: .8rem 0 .25rem; font-size: 1rem; font-weight: 800; }
.feature span { font-size: .86rem; color: var(--muted); line-height: 1.5; display:block; }

.topbar { margin-bottom: 1rem; }
.topbar h2 { margin:0; font-size: 1.25rem; font-weight: 800; }
.topbar p { margin:.15rem 0 0; color: var(--muted); font-size: .88rem; }

/* ---------- chat messages ---------- */
div[data-testid="stChatMessage"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1rem 1.2rem;
    margin-bottom: .9rem;
    box-shadow: var(--shadow);
}
div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: var(--brand-soft);
    border-color: #bfe6e1;
    box-shadow: none;
}
div[data-testid="stChatMessage"] p { line-height: 1.65; font-size: 1rem; }

/* ---------- tool chips ---------- */
.tool-chip {
    display:inline-flex; align-items:center; gap:.5rem; margin: .1rem 0 .8rem 3.2rem;
    padding: .4rem .9rem; border-radius: 999px; font-size: .8rem; font-weight: 600;
    background: var(--blue-soft); color: #4338ca;
}
.tool-chip.buy { background: var(--amber-soft); color: var(--amber); }
.tool-chip code { font-family: 'JetBrains Mono', monospace; background: transparent; color: inherit; font-size: .76rem; }

/* ---------- stock card ---------- */
.stock-card {
    margin: .2rem 0 1.1rem 3.2rem; padding: 1.3rem 1.5rem; border-radius: 22px;
    background: var(--card); border: 1px solid var(--border); box-shadow: var(--shadow);
}
.stock-head { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; }
.stock-sym { font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; }
.stock-sub { font-size: .76rem; color: var(--muted); font-weight: 600; }
.stock-price { font-size: 2.1rem; font-weight: 800; text-align: right; letter-spacing: -.02em; }
.chg {
    display:inline-flex; align-items:center; gap:.3rem; float:right;
    font-size: .88rem; font-weight: 700; padding:.2rem .7rem; border-radius: 999px;
}
.chg.up { color: var(--green); background: var(--green-soft); }
.chg.down { color: var(--red); background: var(--red-soft); }
.stock-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap:.7rem; margin-top: 1.2rem; clear: both; }
.stat { background: var(--soft); border-radius: 14px; padding: .7rem .85rem; }
.stat b { display:block; font-size: 1rem; font-weight: 800; }
.stat span { font-size: .74rem; color: var(--muted); font-weight: 600; }
@media (max-width: 640px){
    .stock-grid{ grid-template-columns: repeat(2,1fr); }
    .stock-card, .tool-chip, .order { margin-left: 0; }
}

/* ---------- order banners ---------- */
.order {
    margin: .2rem 0 1.1rem 3.2rem; padding: 1rem 1.2rem; border-radius: 18px;
    display:flex; gap:.9rem; align-items:center;
}
.order.ok { background: var(--green-soft); border: 1px solid #bfe7cd; }
.order.no { background: var(--red-soft);   border: 1px solid #f5c2c2; }
.order b { display:block; font-size: 1rem; font-weight: 800; }
.order small { color: var(--muted); font-size: .88rem; }

/* ---------- approval card ---------- */
.approval {
    margin: .6rem 0 .8rem; padding: 1.5rem 1.6rem; border-radius: 24px;
    background: var(--amber-soft); border: 1.5px solid #f3d29a;
    box-shadow: 0 10px 30px rgba(217,119,6,.12);
}
.approval .head { display:flex; align-items:center; gap:.8rem; }
.approval h3 { margin: 0; font-size: 1.3rem; font-weight: 800; }
.approval p { margin:.8rem 0 0; color: #7a5a1f; font-size: .95rem; line-height: 1.55; }
.approval .pair { display:flex; gap:.8rem; margin-top: 1rem; flex-wrap: wrap; }
.approval .pair div { background: #fff; border-radius: 14px; padding:.6rem 1.1rem; min-width: 120px; }
.approval .pair b { display:block; font-size:1.3rem; font-weight: 800; }
.approval .pair span { font-size:.76rem; color: var(--muted); font-weight: 600; }

/* main-area buttons (approve / cancel) */
div[data-testid="stMain"] .stButton > button {
    border-radius: 16px; font-weight: 700; font-size: 1rem; padding: .75rem 1rem;
    border: 1.5px solid var(--border); background: var(--card); color: var(--text);
    transition: all .15s ease;
}
div[data-testid="stMain"] .stButton > button[kind="primary"] {
    background: var(--brand); border-color: var(--brand); color: #fff;
    box-shadow: 0 6px 16px rgba(13,148,136,.28);
}
div[data-testid="stMain"] .stButton > button[kind="primary"]:hover { background: var(--brand-dark); transform: translateY(-1px); }
div[data-testid="stMain"] .stButton > button[kind="secondary"]:hover { border-color: var(--red); color: var(--red); }

/* chat input */
div[data-testid="stChatInput"] {
    background: var(--card); border: 1.5px solid var(--border); border-radius: 20px;
    box-shadow: var(--shadow);
}
div[data-testid="stChatInput"] textarea { color: var(--text); }
div[data-testid="stChatInput"]:focus-within { border-color: var(--brand); box-shadow: 0 0 0 4px rgba(13,148,136,.15); }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------
# Backend (loaded once, so MemorySaver persists across reruns)
# ------------------------------------------------------------------
@st.cache_resource(show_spinner="Getting things ready...")
def get_chatbot():
    from backend import chatbot  # backend.py must be in the same folder
    return chatbot


# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
def init_state():
    ss = st.session_state
    ss.setdefault("thread_id", f"thread-{uuid.uuid4().hex[:8]}")
    ss.setdefault("history", [])       # list of UI events
    ss.setdefault("seen_ids", set())   # LangChain message ids already rendered
    ss.setdefault("pending", None)     # pending approval dict
    ss.setdefault("queued_prompt", None)


init_state()
ss = st.session_state


def reset_chat():
    ss.thread_id = f"thread-{uuid.uuid4().hex[:8]}"
    ss.history = []
    ss.seen_ids = set()
    ss.pending = None
    ss.queued_prompt = None


# ------------------------------------------------------------------
# Graph helpers
# ------------------------------------------------------------------
def collect_events(messages):
    """Turn new LangChain messages into UI events (deduped by message id)."""
    events = []
    for m in messages:
        mid = getattr(m, "id", None)
        if mid:
            if mid in ss.seen_ids:
                continue
            ss.seen_ids.add(mid)

        if isinstance(m, HumanMessage):
            continue
        if isinstance(m, AIMessage):
            for call in m.tool_calls or []:
                events.append({"type": "tool_call", "name": call["name"], "args": call["args"]})
            if m.content:
                events.append({"type": "assistant", "content": m.content})
        elif isinstance(m, ToolMessage):
            events.append({"type": "tool_result", "name": m.name, "content": m.content})
    return events


def parse_interrupt(value):
    """Pull symbol and quantity out of the interrupt prompt for the approval card."""
    text = str(value)
    match = re.search(r"buying\s+(\d+)\s+shares\s+of\s+([\w.\-]+)", text, re.I)
    return {
        "prompt": text,
        "quantity": match.group(1) if match else "-",
        "symbol": match.group(2).upper() if match else "-",
    }


def run_graph(payload):
    chatbot = get_chatbot()
    config = {"configurable": {"thread_id": ss.thread_id}}
    try:
        result = chatbot.invoke(payload, config=config)
    except Exception as e:
        ss.history.append({"type": "error", "content": f"{type(e).__name__}: {e}"})
        ss.pending = None
        return

    ss.history.extend(collect_events(result["messages"]))
    interrupts = result.get("__interrupt__", [])
    ss.pending = parse_interrupt(interrupts[0].value) if interrupts else None


# ------------------------------------------------------------------
# Renderers
# ------------------------------------------------------------------
def safe_json(s):
    try:
        return json.loads(s) if isinstance(s, str) else s
    except Exception:
        return None


def fmt_num(v, prefix="", digits=2):
    try:
        return f"{prefix}{float(v):,.{digits}f}"
    except Exception:
        return "-"


def render_stock_card(content):
    data = safe_json(content) or {}
    q = data.get("Global Quote") or {}
    if not q:
        note = data.get("Note") or data.get("Information") or "No quote data came back for that symbol."
        st.markdown(
            f"""
            <div class="order no">
              <span class="ico-badge ico-red">{icon("alert", 22)}</span>
              <div><b>I could not get that quote</b><small>{html.escape(str(note))}</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    change = q.get("09. change", "0")
    pct = q.get("10. change percent", "0%")
    try:
        up = float(change) >= 0
    except Exception:
        up = True
    cls = "up" if up else "down"
    arrow = icon("up" if up else "down", 14)

    st.markdown(
        f"""
        <div class="stock-card">
          <div class="stock-head">
            <div>
              <div class="stock-sub">Latest price</div>
              <div class="stock-sym">{html.escape(q.get("01. symbol", "-"))}</div>
            </div>
            <div>
              <div class="stock-price">{fmt_num(q.get("05. price"), "$")}</div>
              <div class="chg {cls}">{arrow}{fmt_num(change)} ({html.escape(pct)})</div>
            </div>
          </div>
          <div class="stock-grid">
            <div class="stat"><span>Open</span><b>{fmt_num(q.get("02. open"), "$")}</b></div>
            <div class="stat"><span>Day high</span><b>{fmt_num(q.get("03. high"), "$")}</b></div>
            <div class="stat"><span>Day low</span><b>{fmt_num(q.get("04. low"), "$")}</b></div>
            <div class="stat"><span>Volume</span><b>{fmt_num(q.get("06. volume"), "", 0)}</b></div>
          </div>
          <div class="stock-sub" style="margin-top:.9rem">
            Previous close {fmt_num(q.get("08. previous close"), "$")}
            &nbsp;|&nbsp; Trading day {html.escape(q.get("07. latest trading day", "-"))}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_order(content):
    data = safe_json(content) or {}
    ok = data.get("status") == "success"
    badge = (
        f'<span class="ico-badge ico-green">{icon("check", 22)}</span>'
        if ok
        else f'<span class="ico-badge ico-red">{icon("x", 22)}</span>'
    )
    title = "Your order is in" if ok else "Order cancelled"
    st.markdown(
        f"""
        <div class="order {'ok' if ok else 'no'}">
          {badge}
          <div><b>{title}</b><small>{html.escape(str(data.get("message", "")))}</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_event(ev):
    t = ev["type"]
    if t == "user":
        with st.chat_message("user"):
            st.markdown(ev["content"])
    elif t == "assistant":
        with st.chat_message("assistant"):
            st.markdown(ev["content"])
    elif t == "tool_call":
        buy = ev["name"] == "purchase_stock"
        label = "Preparing your order" if buy else "Looking up the price"
        args = ", ".join(f"{k}={v}" for k, v in ev["args"].items())
        st.markdown(
            f'<div class="tool-chip {"buy" if buy else ""}">{icon("cart" if buy else "search", 16)}'
            f'{label} <code>{html.escape(args)}</code></div>',
            unsafe_allow_html=True,
        )
    elif t == "tool_result":
        if ev["name"] == "get_stock_price":
            render_stock_card(ev["content"])
        elif ev["name"] == "purchase_stock":
            render_order(ev["content"])
    elif t == "error":
        st.error(f"Something went wrong: {ev['content']}")


def render_hero():
    st.markdown(
        f"""
        <div class="hero">
          <div class="greet">Welcome back</div>
          <h1>Hi there, how can I <span>help</span> today?</h1>
          <p>Ask me for a live stock price or place a practice order. I will always check with you before anything is bought.</p>
          <div class="feature-row">
            <div class="feature">
              <span class="ico-badge ico-teal">{icon("chart", 22)}</span>
              <h4>Live prices</h4>
              <span>Get the latest price, daily range and volume for any ticker.</span>
            </div>
            <div class="feature">
              <span class="ico-badge ico-amber">{icon("shield", 22)}</span>
              <h4>You stay in control</h4>
              <span>Every purchase waits for your yes before it goes through.</span>
            </div>
            <div class="feature">
              <span class="ico-badge ico-blue">{icon("chat", 22)}</span>
              <h4>Natural conversation</h4>
              <span>I remember what we talked about, so follow-up questions just work.</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="brand">
          <div class="brand-logo">{icon("chart", 24)}</div>
          <div><div class="brand-name">StockPilot</div>
          <div class="brand-sub">Your friendly market helper</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    waiting = ss.pending is not None
    st.markdown(
        f'<span class="status-pill {"wait" if waiting else ""}"><span class="dot"></span>'
        f'{"Waiting for your OK" if waiting else "Ready to help"}</span>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">Quick questions</div>', unsafe_allow_html=True)
    suggestions = [
        "What's the price of AAPL?",
        "Show me TSLA's latest quote",
        "Buy 10 shares of MSFT",
        "Check NVDA and buy 5 shares",
    ]
    for s in suggestions:
        if st.button(s, key=f"sugg_{s}", disabled=waiting):
            ss.queued_prompt = s
            st.rerun()

    st.markdown('<div class="side-label">This conversation</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="meta-box">Session ID<br><code>{ss.thread_id}</code></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Start a new conversation"):
        reset_chat()
        st.rerun()


# ------------------------------------------------------------------
# Main area
# ------------------------------------------------------------------
if ss.history:
    st.markdown(
        '<div class="topbar"><h2>Our conversation</h2>'
        "<p>Ask anything about a stock, or tell me what you would like to buy.</p></div>",
        unsafe_allow_html=True,
    )
else:
    render_hero()

for ev in ss.history:
    render_event(ev)

# ---- Approval step ----
if ss.pending:
    p = ss.pending
    st.markdown(
        f"""
        <div class="approval">
          <div class="head">
            <span class="ico-badge ico-amber" style="background:#fff">{icon("pause", 22)}</span>
            <h3>Please confirm your order</h3>
          </div>
          <p>You asked me to buy <b>{html.escape(p["quantity"])}</b> shares of
             <b>{html.escape(p["symbol"])}</b>. Nothing is purchased until you say yes.</p>
          <div class="pair">
            <div><span>Symbol</span><b>{html.escape(p["symbol"])}</b></div>
            <div><span>Shares</span><b>{html.escape(p["quantity"])}</b></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        approve = st.button("Yes, place the order", type="primary", use_container_width=True)
    with c2:
        reject = st.button("No, cancel it", type="secondary", use_container_width=True)

    if approve or reject:
        decision = "yes" if approve else "no"
        with st.spinner("Got it, one moment..."):
            run_graph(Command(resume=decision))
        st.rerun()

# ---- Chat input ----
typed = st.chat_input(
    "Please confirm or cancel the order above to keep chatting"
    if ss.pending
    else "Type a message, for example: What's the price of AAPL?",
    disabled=ss.pending is not None,
)
prompt = typed or ss.queued_prompt
ss.queued_prompt = None

if prompt:
    ss.history.append({"type": "user", "content": prompt})
    with st.spinner("Let me check that for you..."):
        run_graph({"messages": [HumanMessage(content=prompt)]})
    st.rerun()
