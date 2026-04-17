"""Section 3 — Intuition: a 1D Gumbel-softmax toy, live in the browser."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

def _gumbel_softmax(logits: np.ndarray, tau: float, rng: np.random.Generator) -> np.ndarray:
    g = -np.log(-np.log(rng.uniform(1e-9, 1 - 1e-9, size=logits.shape)))
    x = (logits + g) / tau
    x = x - x.max()
    e = np.exp(x)
    return e / e.sum()


def render():
    st.markdown(
        '<p class="section-lede">'
        "The sensor-placement optimiser needs to pick <em>k</em> candidate points out of thousands. You can't "
        "back-propagate through a <code>argmax</code>. The Gumbel-softmax gives you a "
        "smooth, <strong>differentiable</strong> relaxation that anneals to a hard pick. "
        "Play with temperature τ below to see it happen."
        "</p>",
        unsafe_allow_html=True,
    )

    col_ctrl, col_vis = st.columns([1, 3])
    with col_ctrl:
        n = st.slider("Candidate points", 10, 80, 30, 5)
        seed = st.number_input("Random seed", 0, 999, 42, 1)
        tau = st.slider("Temperature τ", 0.05, 5.0, 1.0, 0.05,
                        help="Anneals from ~5 to ~0.01 over training. Drag it to feel it.")
        hard = st.checkbox("Hard sample (straight-through)", value=False)

    rng = np.random.default_rng(int(seed))
    xs = np.linspace(0, 10, int(n))
    logits = np.random.default_rng(int(seed) + 1000).normal(0, 1.2, int(n))

    draws = np.stack([_gumbel_softmax(logits, tau, rng) for _ in range(6)])
    mean_prob = draws.mean(0)
    hard_idx = draws.argmax(axis=1)

    with col_vis:
        fig = go.Figure()

        # logits as thin grey bars (ghost)
        norm_logits = (logits - logits.min()) / (logits.max() - logits.min() + 1e-9)
        fig.add_trace(go.Bar(
            x=xs, y=norm_logits,
            marker_color="rgba(98,109,121,.22)",
            name="Logits (scaled)",
            hovertemplate="logit=%{customdata:.2f}<extra></extra>",
            customdata=logits,
        ))

        # averaged Gumbel-softmax distribution
        fig.add_trace(go.Scatter(
            x=xs, y=mean_prob,
            mode="lines", line=dict(color="#c44536", width=3),
            name=f"p(x) at τ={tau:.2f}",
            fill="tozeroy", fillcolor="rgba(196,69,54,.12)",
            hovertemplate="p=%{y:.3f}<extra></extra>",
        ))

        # hard samples as stars
        if hard:
            fig.add_trace(go.Scatter(
                x=xs[hard_idx], y=[max(mean_prob) * 1.08] * len(hard_idx),
                mode="markers",
                marker=dict(size=13, color="#1e7770", symbol="star",
                            line=dict(width=1, color="white")),
                name="Hard samples (6 draws)",
                hovertemplate="picked x=%{x:.2f}<extra></extra>",
            ))

        fig.update_layout(
            height=360,
            margin=dict(l=40, r=20, t=20, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Manrope, sans-serif", color="#1f2630"),
            xaxis=dict(title="Candidate location (1D toy)",
                       gridcolor="rgba(31,38,48,.06)", zeroline=False),
            yaxis=dict(title="Probability / scaled logit",
                       gridcolor="rgba(31,38,48,.06)", zeroline=False),
            legend=dict(orientation="h", y=1.12, x=0),
            bargap=0.15,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        '<div class="callout">'
        "<strong>Why this matters.</strong> At high τ the curve is diffuse — sensors spread "
        "out, gradient info flows everywhere. As τ → 0 the curve sharpens to a delta "
        "at the argmax — training commits to a discrete placement. The Gumbel-softmax (GD-MI) optimiser runs exactly "
        "this annealing schedule (τ: 5 → 0.01 over 200 iters) and does it in 2D on the "
        "actual Indian grid."
        "</div>",
        unsafe_allow_html=True,
    )
