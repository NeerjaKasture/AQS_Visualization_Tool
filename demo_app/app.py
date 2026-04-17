"""Air-quality sensor deployment — decision-grade demo.

Single-page scroll UI styled after the interactive-articles site
(~/git/interactive). Loads only precomputed artefacts — no torch, no GPU.

Run:
    streamlit run app.py
"""

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from sections.overview import render as render_overview
from sections.compare import render as render_compare
from sections.state import render as render_state
from sections.download import render as render_download
from sections.intuition import render as render_intuition
from theme import inject_css


st.set_page_config(
    page_title="Fair Sensor Deployment · India",
    page_icon="·",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

inject_css()


def _hero():
    st.markdown(
        """
<div class="hero">
  <p class="eyebrow">Air Quality Sensor Deployment · India</p>
  <h1 class="hero-title">Where should the next <span class="accent">1,000 sensors</span> go?</h1>
  <p class="lede">
    India's CPCB network of a few hundred continuous ambient stations covers
    1.4&nbsp;billion people — poorly, and unevenly. This demo compares deployment
    strategies head-to-head on real held-out PM<sub>2.5</sub>, shows who gets
    covered, and lets a state board walk away with a ready-to-install plan.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )


def _footer():
    st.markdown(
        """
<footer class="site-footer">
  <div>
    <strong>Fair Sensor Deployment Demo</strong> — IIT Gandhinagar Sustainability Lab<br>
    Methods: Gumbel-softmax (GD-MI) · Greedy MaxVar · Metrics on CPCB held-out set.
  </div>
  <div>
    Contact: <a href="mailto:nipun.batra@iitgn.ac.in">nipun.batra@iitgn.ac.in</a>
  </div>
</footer>
        """,
        unsafe_allow_html=True,
    )


def _tab_header(eyebrow: str, title: str, lede: str = ""):
    st.markdown(
        f'<div class="tab-header">'
        f'<span class="tab-eyebrow">{eyebrow}</span>'
        f'<h2 class="section-title">{title}</h2>'
        + (f'<p class="section-lede">{lede}</p>' if lede else '')
        + '</div>',
        unsafe_allow_html=True,
    )


def main():
    _hero()

    tabs = st.tabs([
        "Overview",
        "Compare strategies",
        "How it works",
        "Fairness by state",
        "Deployment plan",
    ])

    with tabs[0]:
        _tab_header("01", "Strategies, at a glance",
                    "Two deployment strategies evaluated on held-out CPCB stations — all numbers real.")
        render_overview()
    with tabs[1]:
        _tab_header("02", "Head-to-head",
                    "Same budget, two strategies. Where do they agree, where do they differ?")
        render_compare()
    with tabs[2]:
        _tab_header("03", "What the optimiser is doing",
                    "Gumbel-softmax in 30 seconds — drag the temperature.")
        render_intuition()
    with tabs[3]:
        _tab_header("04", "Who gets covered?",
                    "Adding a population weight to the loss — does it actually shift sensors toward people?")
        render_state()
    with tabs[4]:
        _tab_header("05", "Export a deployment plan",
                    "Pick a strategy and budget. Walk away with a zip ready for a state board.")
        render_download()

    _footer()


if __name__ == "__main__":
    main()
