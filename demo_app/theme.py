"""Single source of truth for the app's visual style.

Palette and typography adapted from ~/git/interactive (Distill-style
interactive articles) with a warm-red accent that matches the lab poster.
"""

import streamlit as st

_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

  :root {
    --bg: #f6f3ed;
    --panel: #fffdf9;
    --panel-soft: #f9f5ee;
    --ink: #1f2630;
    --muted: #626d79;
    --border: rgba(31, 38, 48, 0.11);
    --accent: #c44536;
    --accent-2: #1e7770;
    --accent-3: #3c68cf;
    --shadow: 0 10px 28px rgba(31, 38, 48, 0.06);
    --shadow-sm: 0 4px 14px rgba(31, 38, 48, 0.04);
    --radius-lg: 22px;
    --radius-md: 16px;
    --font-serif: 'Source Serif 4', Georgia, serif;
    --font-sans: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
  }

  /* reset Streamlit chrome */
  html, body, [class*="css"] { font-family: var(--font-sans); color: var(--ink); }
  .stApp { background: var(--bg); }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stSidebar"] { display: none; }
  .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 5rem; }
  #MainMenu, footer[class*="st"] { visibility: hidden; }

  /* ---------- hero ---------- */
  .hero {
    padding: 2.5rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
  }
  .eyebrow {
    margin: 0 0 .6rem;
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .16em;
    color: var(--muted);
    font-weight: 600;
  }
  .hero-title {
    font-family: var(--font-serif);
    font-weight: 700;
    font-size: clamp(2.4rem, 5.5vw, 4.2rem);
    line-height: 1.04;
    letter-spacing: -0.03em;
    margin: 0 0 1.2rem;
    max-width: 22ch;
  }
  .hero-title .accent { color: var(--accent); }
  .lede {
    max-width: 64ch;
    font-size: 1.12rem;
    color: #3a4350;
    line-height: 1.6;
    margin: 0 0 1.8rem;
  }
  .hero-stats { display: flex; gap: 2.4rem; flex-wrap: wrap; }
  .stat { display: flex; flex-direction: column; gap: .25rem; }
  .stat .num {
    font-family: var(--font-serif);
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink);
  }
  .stat .lbl {
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: var(--muted);
  }

  /* ---------- nav ---------- */
  .section-nav {
    display: flex; flex-wrap: wrap; gap: 1.5rem;
    padding: 1rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
    font-size: .88rem;
  }
  .section-nav a {
    color: var(--muted);
    text-decoration: none;
    font-weight: 500;
    transition: color .15s;
  }
  .section-nav a:hover { color: var(--accent); }

  /* ---------- step sections ---------- */
  .step-section {
    position: relative;
    margin: 2.4rem 0;
    padding: 2.6rem 2.2rem;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow);
  }
  .step-badge {
    position: absolute;
    top: -14px;
    left: 32px;
    background: var(--accent);
    color: white;
    font-family: var(--font-sans);
    font-weight: 700;
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .12em;
    padding: .38rem 1rem;
    border-radius: 999px;
    box-shadow: 0 4px 12px rgba(196, 69, 54, .22);
  }
  .section-title {
    font-family: var(--font-serif);
    font-weight: 700;
    font-size: clamp(1.6rem, 3vw, 2.2rem);
    letter-spacing: -0.02em;
    margin: 0 0 1.5rem;
    color: var(--ink);
  }
  .section-lede {
    font-size: 1.02rem;
    color: #3a4350;
    max-width: 68ch;
    margin: 0 0 1.6rem;
  }

  /* ---------- widgets ---------- */
  .stSelectbox label, .stSlider label, .stNumberInput label, .stRadio label,
  .stCheckbox label, .stMultiSelect label {
    font-size: .8rem !important;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted) !important;
    font-weight: 600 !important;
  }
  .stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
  }
  .stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--accent) !important;
  }
  .stButton > button {
    background: var(--ink);
    color: white;
    border: none;
    border-radius: 10px;
    padding: .55rem 1.3rem;
    font-family: var(--font-sans);
    font-weight: 600;
    font-size: .9rem;
    transition: transform .1s, background .15s;
  }
  .stButton > button:hover { background: var(--accent); transform: translateY(-1px); }
  .stDownloadButton > button {
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 10px;
    padding: .6rem 1.4rem;
    font-weight: 600;
  }
  .stDownloadButton > button:hover { background: #a83a2d; }

  /* ---------- metrics ---------- */
  [data-testid="stMetricValue"] {
    font-family: var(--font-serif);
    font-weight: 700;
    font-size: 1.9rem;
    color: var(--ink);
  }
  [data-testid="stMetricLabel"] {
    font-size: .72rem !important;
    text-transform: uppercase;
    letter-spacing: .1em;
    color: var(--muted) !important;
  }
  [data-testid="stMetricDelta"] { font-family: var(--font-mono); font-size: .8rem; }

  /* ---------- tables ---------- */
  .stDataFrame, .stTable {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--panel) !important;
    box-shadow: var(--shadow-sm);
  }
  .stDataFrame [data-testid="stTable"] { font-family: var(--font-sans); }

  /* ---------- plotly ---------- */
  .js-plotly-plot { border-radius: var(--radius-md); }

  /* ---------- custom callouts ---------- */
  .callout {
    padding: 1rem 1.2rem;
    border-left: 3px solid var(--accent-2);
    background: var(--panel-soft);
    border-radius: 6px;
    margin: 1rem 0;
    font-size: .95rem;
    color: #3a4350;
  }
  .callout.warn { border-left-color: var(--accent); }

  /* ---------- footer ---------- */
  .site-footer {
    margin-top: 4rem;
    padding: 2rem 0 1rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    gap: 2rem;
    flex-wrap: wrap;
    font-size: .85rem;
    color: var(--muted);
  }
  .site-footer a { color: var(--accent); text-decoration: none; }
  .site-footer a:hover { text-decoration: underline; }

  /* ---------- tabs ---------- */
  .stTabs { margin-top: 1rem; }
  .stTabs [data-baseweb="tab-list"] {
    gap: .2rem;
    border-bottom: 1px solid var(--border);
    background: transparent;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    padding: .85rem 1.3rem;
    font-weight: 600;
    font-size: .95rem;
    color: var(--muted);
    border-radius: 0;
  }
  .stTabs [data-baseweb="tab"]:hover { color: var(--ink); }
  .stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none; }
  .stTabs [data-baseweb="tab-panel"] {
    padding: 2rem 0 1rem;
  }

  .tab-header { margin: .5rem 0 1.8rem; }
  .tab-eyebrow {
    display: inline-block;
    background: var(--accent);
    color: white;
    font-weight: 700;
    font-size: .7rem;
    letter-spacing: .12em;
    padding: .3rem .9rem;
    border-radius: 999px;
    margin-bottom: .8rem;
  }

  /* big number in cards */
  .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1rem 0; }
  .num-card {
    background: var(--panel-soft);
    padding: 1.2rem 1.4rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
  }
  .num-card .k { font-family: var(--font-serif); font-size: 2rem; font-weight: 700; letter-spacing: -.02em; }
  .num-card .l { font-size: .75rem; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-top: .2rem; }
  .num-card.accent .k { color: var(--accent); }
  .num-card.green .k { color: var(--accent-2); }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def num_card(value: str, label: str, kind: str = "") -> str:
    """Return HTML for a big-number card. kind in {"", "accent", "green"}."""
    return f'<div class="num-card {kind}"><div class="k">{value}</div><div class="l">{label}</div></div>'


def callout(text: str, warn: bool = False) -> str:
    cls = "callout warn" if warn else "callout"
    return f'<div class="{cls}">{text}</div>'
