"""
neurisk/neurisk_ui.py
─────────────────────
Production-grade Streamlit UI for the NeuroRisk GRC tab.
Called by app.py with:  from neurisk.neurisk_ui import render_neurisk_tab
                        render_neurisk_tab()
"""

import re
import streamlit as st
from neurisk.rag_engine import (
    load_frameworks, add_company_doc, get_company_docs, get_frameworks,
    company_has_docs, clear_company_docs, extract_uploaded_file,
    gap_analysis, compliance_chat, FRAMEWORKS,
)


# ── CSS ───────────────────────────────────────────────────────────────────────
def _inject_nr_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&display=swap');
    /* ── Gap Analysis font size overrides ── */
.nr-bar-label            { font-size: 15px !important; }
.nr-bar-meta span        { font-size: 13px !important; }
div[data-testid="stExpander"] div[style*="border-left:2px solid var(--success-border)"],
div[data-testid="stExpander"] div[style*="border-left:2px solid var(--warning-border)"] {
    font-size: 15px !important;
}
    /* ═══════════════════════════════════════════
       DESIGN TOKENS
    ═══════════════════════════════════════════ */
    :root {
        /* Backgrounds */
        --bg-base:        #060910;
        --bg-layer-1:     #0b0f1a;
        --bg-layer-2:     #0f1520;
        --bg-layer-3:     #141c2b;
        --bg-layer-4:     #192234;

        /* Borders */
        --border-subtle:  rgba(255,255,255,0.055);
        --border-default: rgba(255,255,255,0.09);
        --border-strong:  rgba(255,255,255,0.15);

        /* Brand — cool blue/cyan */
        --brand:          #3b8dff;
        --brand-light:    #60a5ff;
        --brand-dim:      rgba(59,141,255,0.12);
        --brand-glow:     rgba(59,141,255,0.22);
        --brand-glow-lg:  rgba(59,141,255,0.08);

        /* Semantic */
        --success:        #22c55e;
        --success-dim:    rgba(34,197,94,0.10);
        --success-border: rgba(34,197,94,0.22);

        --warning:        #f59e0b;
        --warning-dim:    rgba(245,158,11,0.10);
        --warning-border: rgba(245,158,11,0.22);

        --danger:         #ef4444;
        --danger-dim:     rgba(239,68,68,0.10);
        --danger-border:  rgba(239,68,68,0.22);

        --info:           #06b6d4;
        --info-dim:       rgba(6,182,212,0.10);
        --info-border:    rgba(6,182,212,0.22);

        /* Typography */
        --text-primary:   #f0f4ff;
        --text-secondary: rgba(240,244,255,0.62);
        --text-tertiary:  rgba(240,244,255,0.36);
        --text-disabled:  rgba(240,244,255,0.22);

        /* Fonts */
        --font-sans: 'DM Sans', system-ui, sans-serif;
        --font-mono: 'DM Mono', monospace;

        /* Radius */
        --r-sm:  6px;
        --r-md:  10px;
        --r-lg:  14px;
        --r-xl:  18px;
        --r-2xl: 24px;

        /* Shadows */
        --shadow-sm:  0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
        --shadow-md:  0 4px 12px rgba(0,0,0,0.45), 0 2px 4px rgba(0,0,0,0.3);
        --shadow-lg:  0 10px 30px rgba(0,0,0,0.5), 0 4px 8px rgba(0,0,0,0.3);
        --shadow-brand: 0 4px 20px rgba(59,141,255,0.18);
    }

    /* ═══════════════════════════════════════════
       BASE RESETS
    ═══════════════════════════════════════════ */
    .neurisk-root {
        font-family: var(--font-sans);
        color: var(--text-primary);
        font-size: 14px;
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
    }

    /* ═══════════════════════════════════════════
       SIDEBAR
    ═══════════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: var(--bg-layer-1) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    /* Brand lockup */
    .nr-brand {
        padding: 24px 20px 20px;
        border-bottom: 1px solid var(--border-subtle);
        margin-bottom: 6px;
    }
    .nr-brand-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }
    .nr-brand-icon {
        width: 32px; height: 32px;
        background: var(--brand-dim);
        border: 1px solid var(--brand-glow);
        border-radius: var(--r-md);
        display: flex; align-items: center; justify-content: center;
        font-size: 15px; line-height: 1;
        box-shadow: var(--shadow-brand);
        flex-shrink: 0;
    }
    .nr-brand-name {
        font-family: var(--font-sans);
        font-size: 17px;
        font-weight: 700;
        letter-spacing: -0.4px;
        color: var(--text-primary);
    }
    .nr-brand-name span { color: var(--brand-light); }
    .nr-brand-tag {
        font-family: var(--font-mono);
        font-size: 9px;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        color: var(--text-disabled);
        padding-left: 42px;
        margin-top: 2px;
    }

    /* Sidebar system status */
    .nr-sys-status {
        margin: 10px 16px 4px;
        padding: 10px 14px;
        background: var(--bg-layer-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-md);
    }
    .nr-sys-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 3px 0;
    }
    .nr-sys-label {
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 0.8px;
        color: var(--text-tertiary);
        text-transform: uppercase;
    }
    .nr-sys-val {
        font-family: var(--font-mono);
        font-size: 11px;
        font-weight: 500;
        color: var(--success);
    }
    .nr-sys-val.warn { color: var(--warning); }
    .nr-sys-val.info { color: var(--brand-light); }

    /* Nav section header */
    .nr-nav-group-label {
        font-family: var(--font-mono);
        font-size: 9px;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        color: var(--text-disabled);
        padding: 16px 20px 6px;
    }

    /* Nav items via st.button */
    .nr-nav-item { padding: 0 10px; margin-bottom: 2px; }
    .nr-nav-item div[data-testid="stButton"] button {
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-family: var(--font-sans) !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 9px 12px !important;
        border-radius: var(--r-md) !important;
        width: 100% !important;
        transition: background 0.15s, color 0.15s !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }
    .nr-nav-item div[data-testid="stButton"] button:hover {
        background: rgba(255,255,255,0.05) !important;
        color: var(--text-primary) !important;
    }
    .nr-nav-item.active div[data-testid="stButton"] button {
        background: var(--brand-dim) !important;
        color: var(--brand-light) !important;
        border: 1px solid var(--brand-glow) !important;
        font-weight: 600 !important;
    }

    /* Sidebar footer */
    .nr-sidebar-footer {
        position: absolute;
        bottom: 0; left: 0; right: 0;
        padding: 14px 20px;
        border-top: 1px solid var(--border-subtle);
        background: var(--bg-layer-1);
    }
    .nr-sidebar-footer-text {
        font-family: var(--font-mono);
        font-size: 9px;
        letter-spacing: 1.2px;
        color: var(--text-disabled);
        text-align: center;
    }

    /* ═══════════════════════════════════════════
       MAIN CONTENT AREA
    ═══════════════════════════════════════════ */
    div[data-testid="stMainBlockContainer"] {
        padding-top: 32px !important;
        padding-bottom: 56px !important;
        max-width: 1100px !important;
    }

    /* ═══════════════════════════════════════════
       PAGE HEADER
    ═══════════════════════════════════════════ */
    .nr-page-header {
        padding-bottom: 24px;
        margin-bottom: 28px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .nr-breadcrumb {
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--text-disabled);
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .nr-breadcrumb-sep { color: var(--border-strong); }
    .nr-breadcrumb-active { color: var(--brand-light); }
    .nr-page-title {
        font-family: var(--font-sans);
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.6px;
        color: var(--text-primary);
        line-height: 1.15;
        margin-bottom: 6px;
    }
    .nr-page-title em {
        color: var(--brand-light);
        font-style: normal;
    }
    .nr-page-sub {
        font-size: 14px;
        color: var(--text-secondary);
        font-weight: 400;
        line-height: 1.5;
    }

    /* ═══════════════════════════════════════════
       METRIC CARDS
    ═══════════════════════════════════════════ */
    .nr-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 12px;
        margin-bottom: 28px;
    }
    .nr-metric-card {
        background: var(--bg-layer-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-lg);
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s, transform 0.2s;
    }
    .nr-metric-card:hover {
        border-color: var(--border-default);
        transform: translateY(-1px);
    }
    /* Top accent bar */
    .nr-metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
        border-radius: var(--r-lg) var(--r-lg) 0 0;
    }
    .nr-metric-card.green::before  { background: linear-gradient(90deg, var(--success), rgba(34,197,94,0.4)); }
    .nr-metric-card.amber::before  { background: linear-gradient(90deg, var(--warning), rgba(245,158,11,0.4)); }
    .nr-metric-card.red::before    { background: linear-gradient(90deg, var(--danger),  rgba(239,68,68,0.4)); }
    .nr-metric-card.blue::before   { background: linear-gradient(90deg, var(--brand),   rgba(59,141,255,0.4)); }
    .nr-metric-card.cyan::before   { background: linear-gradient(90deg, var(--info),    rgba(6,182,212,0.4)); }

    .nr-metric-icon {
        font-size: 18px;
        margin-bottom: 10px;
        opacity: 0.7;
    }
    .nr-metric-val {
        font-family: var(--font-mono);
        font-size: 28px;
        font-weight: 500;
        line-height: 1;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
    }
    .nr-metric-val.green { color: var(--success); }
    .nr-metric-val.amber { color: var(--warning); }
    .nr-metric-val.red   { color: var(--danger); }
    .nr-metric-val.blue  { color: var(--brand-light); }
    .nr-metric-val.cyan  { color: var(--info); }

    .nr-metric-lbl {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: 0.1px;
        margin-bottom: 2px;
    }
    .nr-metric-sub {
        font-size: 11px;
        color: var(--text-tertiary);
        font-weight: 400;
    }

    /* ═══════════════════════════════════════════
       SECTION LABELS
    ═══════════════════════════════════════════ */
    .nr-section-title {
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        color: var(--text-tertiary);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-subtle);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nr-section-title::before {
        content: '';
        display: inline-block;
        width: 3px; height: 12px;
        background: var(--brand);
        border-radius: 2px;
        flex-shrink: 0;
    }

    /* ═══════════════════════════════════════════
       DIVIDER
    ═══════════════════════════════════════════ */
    .nr-divider {
        border: none;
        border-top: 1px solid var(--border-subtle);
        margin: 28px 0;
    }

    /* ═══════════════════════════════════════════
       CARDS
    ═══════════════════════════════════════════ */
    .nr-card {
        background: var(--bg-layer-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-lg);
        padding: 18px 20px;
        margin-bottom: 10px;
        transition: border-color 0.2s;
    }
    .nr-card:hover { border-color: var(--border-default); }
    .nr-card.green { border-left: 3px solid var(--success); }
    .nr-card.amber { border-left: 3px solid var(--warning); }
    .nr-card.red   { border-left: 3px solid var(--danger); }
    .nr-card.blue  { border-left: 3px solid var(--brand); }
    .nr-card.cyan  { border-left: 3px solid var(--info); }

    /* ═══════════════════════════════════════════
       TAGS / BADGES
    ═══════════════════════════════════════════ */
    .nr-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 500;
        letter-spacing: 0.4px;
        padding: 3px 9px;
        border-radius: 20px;
        white-space: nowrap;
    }
    .nr-tag.green {
        background: var(--success-dim);
        color: var(--success);
        border: 1px solid var(--success-border);
    }
    .nr-tag.amber {
        background: var(--warning-dim);
        color: var(--warning);
        border: 1px solid var(--warning-border);
    }
    .nr-tag.red {
        background: var(--danger-dim);
        color: var(--danger);
        border: 1px solid var(--danger-border);
    }
    .nr-tag.blue {
        background: var(--brand-dim);
        color: var(--brand-light);
        border: 1px solid var(--brand-glow);
    }
    .nr-tag.cyan {
        background: var(--info-dim);
        color: var(--info);
        border: 1px solid var(--info-border);
    }

    /* ═══════════════════════════════════════════
       PILLS (framework chips)
    ═══════════════════════════════════════════ */
    .nr-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 20px;
    }
    .nr-pill {
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 500;
        letter-spacing: 0.3px;
        padding: 4px 11px;
        border-radius: 20px;
        transition: all 0.15s;
    }
    .nr-pill.on {
        background: var(--brand-dim);
        color: var(--brand-light);
        border: 1px solid var(--brand-glow);
    }
    .nr-pill.off {
        background: rgba(255,255,255,0.03);
        color: var(--text-disabled);
        border: 1px solid var(--border-subtle);
    }

    /* ═══════════════════════════════════════════
       ALERT BANNERS
    ═══════════════════════════════════════════ */
    .nr-alert {
        padding: 12px 16px;
        border-radius: var(--r-md);
        font-size: 13px;
        font-family: var(--font-sans);
        line-height: 1.6;
        margin-bottom: 14px;
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }
    .nr-alert-icon { flex-shrink: 0; font-size: 14px; margin-top: 1px; }
    .nr-alert.info {
        background: var(--info-dim);
        border: 1px solid var(--info-border);
        color: rgba(6,182,212,0.9);
    }
    .nr-alert.warn {
        background: var(--warning-dim);
        border: 1px solid var(--warning-border);
        color: rgba(245,158,11,0.9);
    }
    .nr-alert.ok {
        background: var(--success-dim);
        border: 1px solid var(--success-border);
        color: rgba(34,197,94,0.9);
    }
    .nr-alert.danger {
        background: var(--danger-dim);
        border: 1px solid var(--danger-border);
        color: rgba(239,68,68,0.9);
    }

    /* ═══════════════════════════════════════════
       PROGRESS BARS
    ═══════════════════════════════════════════ */
    .nr-bar-wrap { margin-bottom: 10px; }
    .nr-bar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .nr-bar-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary);
    }
    .nr-bar-meta {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nr-bar-track {
        background: rgba(255,255,255,0.05);
        border-radius: 4px;
        height: 5px;
        overflow: hidden;
    }
    .nr-bar-fill {
        height: 5px;
        border-radius: 4px;
        transition: width 0.7s cubic-bezier(.4,0,.2,1);
    }

    /* ═══════════════════════════════════════════
       FRAMEWORK GRID (overview)
    ═══════════════════════════════════════════ */
    .nr-fw-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 8px;
        margin-bottom: 20px;
    }
    .nr-fw-item {
        background: var(--bg-layer-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-md);
        padding: 12px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: border-color 0.15s;
    }
    .nr-fw-item:hover { border-color: var(--border-default); }
    .nr-fw-item.loaded { border-left: 3px solid var(--success); }
    .nr-fw-item.missing { border-left: 3px solid var(--border-subtle); opacity: 0.5; }
    .nr-fw-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .nr-fw-item.loaded  .nr-fw-dot { background: var(--success); box-shadow: 0 0 6px rgba(34,197,94,0.5); }
    .nr-fw-item.missing .nr-fw-dot { background: var(--text-disabled); }
    .nr-fw-item-name {
        font-size: 12.5px;
        font-weight: 500;
        color: var(--text-primary);
        flex: 1;
    }
    .nr-fw-item-status {
        font-family: var(--font-mono);
        font-size: 9px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .nr-fw-item.loaded  .nr-fw-item-status { color: var(--success); }
    .nr-fw-item.missing .nr-fw-item-status { color: var(--text-disabled); }

    /* ═══════════════════════════════════════════
       DOCUMENT ROWS
    ═══════════════════════════════════════════ */
    .nr-doc-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: var(--bg-layer-2);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-md);
        margin-bottom: 6px;
        transition: border-color 0.15s;
    }
    .nr-doc-row:hover { border-color: var(--border-default); }
    .nr-doc-left { display: flex; align-items: center; gap: 10px; }
    .nr-doc-icon {
        width: 28px; height: 28px;
        background: var(--bg-layer-3);
        border: 1px solid var(--border-subtle);
        border-radius: var(--r-sm);
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; flex-shrink: 0;
    }
    .nr-doc-name {
        font-size: 13px;
        font-weight: 500;
        color: var(--text-primary);
    }
    .nr-doc-meta {
        font-family: var(--font-mono);
        font-size: 10px;
        color: var(--text-tertiary);
    }

    /* ═══════════════════════════════════════════
       CHAT BUBBLES
    ═══════════════════════════════════════════ */
    .nr-chat-wrap {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 16px;
    }
    .nr-bubble {
        max-width: 80%;
        padding: 12px 16px;
        font-size: 14px;
        line-height: 1.7;
        border-radius: var(--r-lg);
    }
    .nr-bubble.user {
        align-self: flex-end;
        background: var(--bg-layer-3);
        border: 1px solid var(--brand-glow);
        color: var(--text-primary);
        margin-left: 20%;
        border-radius: var(--r-lg) var(--r-lg) var(--r-sm) var(--r-lg);
    }
    .nr-bubble.ai {
        align-self: flex-start;
        background: var(--bg-layer-2);
        border: 1px solid var(--border-subtle);
        border-left: 2px solid var(--brand);
        color: var(--text-secondary);
        margin-right: 20%;
        border-radius: var(--r-sm) var(--r-lg) var(--r-lg) var(--r-lg);
    }
    .nr-bubble-sender {
        font-family: var(--font-mono);
        font-size: 9px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .nr-bubble.user .nr-bubble-sender { color: rgba(59,141,255,0.55); text-align: right; }
    .nr-bubble.ai   .nr-bubble-sender { color: rgba(34,197,94,0.55); }

    /* ═══════════════════════════════════════════
       SUGGESTED Q BUTTONS
    ═══════════════════════════════════════════ */
    .nr-sug-grid div[data-testid="stButton"] button {
        background: var(--bg-layer-2) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-secondary) !important;
        font-family: var(--font-sans) !important;
        font-size: 12.5px !important;
        font-weight: 400 !important;
        text-align: left !important;
        white-space: normal !important;
        height: auto !important;
        padding: 11px 14px !important;
        border-radius: var(--r-md) !important;
        transition: all 0.15s !important;
        line-height: 1.5 !important;
    }
    .nr-sug-grid div[data-testid="stButton"] button:hover {
        background: var(--brand-dim) !important;
        border-color: var(--brand-glow) !important;
        color: var(--text-primary) !important;
    }

    /* ═══════════════════════════════════════════
       STREAMLIT COMPONENT OVERRIDES
    ═══════════════════════════════════════════ */

    /* Text inputs */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background: var(--bg-layer-2) !important;
        border: 1px solid var(--border-default) !important;
        color: var(--text-primary) !important;
        border-radius: var(--r-md) !important;
        font-family: var(--font-sans) !important;
        font-size: 13.5px !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--brand) !important;
        box-shadow: 0 0 0 3px var(--brand-glow-lg) !important;
        outline: none !important;
    }

    /* Select / multiselect */
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stMultiSelect"] > div {
        background: var(--bg-layer-2) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--r-md) !important;
        font-family: var(--font-sans) !important;
    }

    /* File uploader */
    div[data-testid="stFileUploader"] {
        background: var(--bg-layer-2) !important;
        border: 1px dashed var(--brand-glow) !important;
        border-radius: var(--r-xl) !important;
        transition: border-color 0.2s !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--brand) !important;
    }

    /* Primary button */
    div[data-testid="stButton"] button[kind="primary"] {
        background: var(--brand) !important;
        color: #fff !important;
        border: none !important;
        border-radius: var(--r-md) !important;
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        letter-spacing: 0.1px !important;
        transition: all 0.18s !important;
        box-shadow: var(--shadow-brand) !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: var(--brand-light) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 24px rgba(59,141,255,0.28) !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:active {
        transform: translateY(0px) !important;
    }

    /* Secondary buttons (default) */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: var(--bg-layer-3) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--r-md) !important;
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
        transition: all 0.15s !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: var(--bg-layer-4) !important;
        border-color: var(--border-strong) !important;
        color: var(--text-primary) !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        background: var(--bg-layer-2) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--r-lg) !important;
    }
    div[data-testid="stExpander"]:hover {
        border-color: var(--border-default) !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: var(--font-sans) !important;
        font-weight: 500 !important;
        color: var(--text-primary) !important;
    }

    /* Chat input */
    div[data-testid="stChatInput"] textarea {
        background: var(--bg-layer-2) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--r-lg) !important;
        color: var(--text-primary) !important;
        font-family: var(--font-sans) !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: var(--brand) !important;
        box-shadow: 0 0 0 3px var(--brand-glow-lg) !important;
    }

    /* Progress */
    .stProgress > div > div {
        background: var(--brand) !important;
        border-radius: 4px !important;
    }
    .stProgress { border-radius: 4px !important; }

    /* Alerts */
    div[data-testid="stAlert"] {
        border-radius: var(--r-md) !important;
        font-family: var(--font-sans) !important;
    }

    /* Labels */
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stFileUploader"] label {
        font-family: var(--font-sans) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
    }

    /* Spinner */
    div[data-testid="stSpinner"] {
        font-family: var(--font-sans) !important;
        color: var(--text-secondary) !important;
    }

    /* Success/info/warning/error messages */
    div[data-testid="stSuccess"] {
        background: var(--success-dim) !important;
        border: 1px solid var(--success-border) !important;
        border-radius: var(--r-md) !important;
        color: var(--success) !important;
    }

    /* ═══════════════════════════════════════════
       HIDE STREAMLIT CHROME
    ═══════════════════════════════════════════ */
    #MainMenu, footer, header { visibility: hidden; }
    div[data-testid="stDecoration"] { display: none !important; }

    /* ═══════════════════════════════════════════
       SCROLLBAR
    ═══════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: var(--border-strong);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }

    </style>
    """, unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fw_pills():
    fw = get_frameworks()
    pills = "".join(
        f"<span class='nr-pill {'on' if name in fw else 'off'}'>{name}</span>"
        for name in FRAMEWORKS
    )
    st.markdown(f"<div class='nr-pills'>{pills}</div>", unsafe_allow_html=True)


def _tag(text, cls="blue"):
    return f"<span class='nr-tag {cls}'>{text}</span>"


def _status_color(s):
    return {"Full": "green", "Partial": "amber", "Gap": "red"}.get(s, "blue")


def _bar_color(pct):
    if pct >= 70: return "var(--success)"
    if pct >= 40: return "var(--warning)"
    return "var(--danger)"


def _page_header(crumb, title_html, subtitle):
    st.markdown(f"""
    <div class='nr-page-header'>
        <div class='nr-breadcrumb'>
            NeuroRisk
            <span class='nr-breadcrumb-sep'>›</span>
            <span class='nr-breadcrumb-active'>{crumb}</span>
        </div>
        <div class='nr-page-title'>{title_html}</div>
        <div class='nr-page-sub'>{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def _section(label):
    st.markdown(f"<div class='nr-section-title'>{label}</div>", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _render_sidebar():
    fw = get_frameworks()
    co = get_company_docs()
    loaded = len(fw)
    total  = len(FRAMEWORKS)
    is_ok  = loaded == total

    with st.sidebar:
        # Brand
        st.markdown(f"""
        <div class='nr-brand'>
            <div class='nr-brand-logo'>
                <div class='nr-brand-icon'>⬡</div>
                <div class='nr-brand-name'>Neuro<span>Risk</span></div>
            </div>
            <div class='nr-brand-tag'>GRC Intelligence Platform</div>
        </div>
        """, unsafe_allow_html=True)

        # System status
        st.markdown(f"""
        <div class='nr-sys-status'>
            <div class='nr-sys-row'>
                <span class='nr-sys-label'>Frameworks</span>
                <span class='nr-sys-val {"" if is_ok else "warn"}'>{loaded}/{total}</span>
            </div>
            <div class='nr-sys-row'>
                <span class='nr-sys-label'>Company Docs</span>
                <span class='nr-sys-val info'>{len(co)}</span>
            </div>
            <div class='nr-sys-row'>
                <span class='nr-sys-label'>Engine</span>
                <span class='nr-sys-val {"" if is_ok else "warn"}'>{"● Ready" if is_ok else "● Partial"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Nav
        st.markdown("<div class='nr-nav-group-label'>Navigation</div>", unsafe_allow_html=True)

        NAV = [
            ("overview", "🏠", "Overview"),
            ("upload",   "📤", "Upload Documents"),
            ("gap",      "🔍", "Gap Analysis"),
            ("chat",     "💬", "Compliance Chat"),
        ]

        cur = st.session_state.get("nr_page", "overview")
        for key, icon, label in NAV:
            active_cls = "active" if cur == key else ""
            st.markdown(f"<div class='nr-nav-item {active_cls}'>", unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nr_nav_{key}", use_container_width=True):
                st.session_state.nr_page = key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div class='nr-sidebar-footer'>
            <div class='nr-sidebar-footer-text'>NeuroRisk · GRC Intelligence · v2.0</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def _page_overview():
    fw     = get_frameworks()
    co     = get_company_docs()
    loaded = len(fw)
    total  = len(FRAMEWORKS)

    _page_header(
        "Overview",
        "Platform <em>Overview</em>",
        f"Compliance intelligence powered by {total} pre-loaded regulatory frameworks"
    )

    # Metrics
    st.markdown(f"""
    <div class='nr-metrics'>
        <div class='nr-metric-card green'>
            <div class='nr-metric-icon'>📦</div>
            <div class='nr-metric-val green'>{loaded}</div>
            <div class='nr-metric-lbl'>Frameworks Loaded</div>
            <div class='nr-metric-sub'>of {total} total</div>
        </div>
        <div class='nr-metric-card blue'>
            <div class='nr-metric-icon'>📄</div>
            <div class='nr-metric-val blue'>{len(co)}</div>
            <div class='nr-metric-lbl'>Company Docs</div>
            <div class='nr-metric-sub'>ready for analysis</div>
        </div>
        <div class='nr-metric-card {'amber' if total - loaded else 'green'}'>
            <div class='nr-metric-icon'>{'⚠️' if total - loaded else '✅'}</div>
            <div class='nr-metric-val {'amber' if total - loaded else 'green'}'>{total - loaded}</div>
            <div class='nr-metric-lbl'>Missing Frameworks</div>
            <div class='nr-metric-sub'>{'action required' if total - loaded else 'all systems go'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Framework status
    _section("REGULATORY FRAMEWORKS")
    _fw_pills()

    if total - loaded:
        missing = [name for name in FRAMEWORKS if name not in fw]
        st.markdown(f"""
        <div class='nr-alert warn'>
            <span class='nr-alert-icon'>⚠</span>
            <div>Missing framework PDFs: <b>{', '.join(missing)}</b><br>
            Place the PDF files in <code>neurisk/documents/</code> and restart the app.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='nr-alert ok'>
            <span class='nr-alert-icon'>✦</span>
            <div>All 8 regulatory frameworks loaded and indexed. NeuroRisk is fully operational.</div>
        </div>
        """, unsafe_allow_html=True)

    # Framework grid
    st.markdown("<div class='nr-fw-grid'>", unsafe_allow_html=True)
    for name in FRAMEWORKS:
        ok = name in fw
        st.markdown(f"""
        <div class='nr-fw-item {'loaded' if ok else 'missing'}'>
            <div class='nr-fw-dot'></div>
            <div class='nr-fw-item-name'>{name}</div>
            <div class='nr-fw-item-status'>{'Loaded' if ok else 'Missing'}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Company docs
    st.markdown("<hr class='nr-divider'>", unsafe_allow_html=True)
    _section("YOUR COMPANY DOCUMENTS")

    if not co:
        st.markdown("""
        <div class='nr-alert warn'>
            <span class='nr-alert-icon'>⚠</span>
            <div>No company documents uploaded yet. Navigate to <b>Upload Documents</b> to get started.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for name, text in co.items():
            st.markdown(f"""
            <div class='nr-doc-row'>
                <div class='nr-doc-left'>
                    <div class='nr-doc-icon'>📄</div>
                    <span class='nr-doc-name'>{name}</span>
                </div>
                <span class='nr-doc-meta'>{len(text):,} chars</span>
            </div>
            """, unsafe_allow_html=True)


def _page_upload():
    _page_header(
        "Upload Documents",
        "Upload <em>Company Documents</em>",
        "Upload your policies, SOPs, and controls — Eva AI will analyse them against all frameworks"
    )

    st.markdown("""
    <div class='nr-alert info'>
        <span class='nr-alert-icon'>📎</span>
        <div>Supported formats: <b>PDF · DOCX · TXT · MD</b> &nbsp;·&nbsp;
        Max 50 MB per file &nbsp;·&nbsp; Documents are session-scoped (not stored permanently)</div>
    </div>
    """, unsafe_allow_html=True)

    _section("COMPANY PROFILE")
    company_name_input = st.text_input(
        "Your company name (used in all analysis reports)",
        value=st.session_state.get("nr_company_name", ""),
        placeholder="e.g. Acme Fintech Pvt. Ltd.",
        key="nr_company_name_input",
    )
    if company_name_input.strip():
        st.session_state.nr_company_name = company_name_input.strip()

    st.markdown("<hr class='nr-divider'>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        _section("FILE UPLOAD")
        uploaded = st.file_uploader(
            "Drop documents here",
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="nr_uploader",
        )

        if uploaded:
            st.markdown(f"""
            <div class='nr-alert ok'>
                <span class='nr-alert-icon'>✓</span>
                <div>{len(uploaded)} file(s) selected and ready to ingest</div>
            </div>
            """, unsafe_allow_html=True)
            labels = {}
            for f in uploaded:
                default_label = (f.name
                                 .replace(".pdf","").replace(".docx","")
                                 .replace(".txt","").replace(".md","")
                                 .replace("_"," ").replace("-"," ").title())
                labels[f.name] = st.text_input(
                    f"Label for **{f.name}**",
                    value=default_label,
                    key=f"nr_label_{f.name}",
                )

            if st.button("⬆  Ingest Documents", type="primary", use_container_width=True, key="nr_ingest"):
                prog = st.progress(0)
                for i, f in enumerate(uploaded):
                    with st.spinner(f"Processing {f.name}…"):
                        f.seek(0)
                        text  = extract_uploaded_file(f)
                        label = labels.get(f.name, f.name)
                        add_company_doc(label, text)
                    prog.progress((i + 1) / len(uploaded))
                st.success(f"✓  {len(uploaded)} document(s) ingested successfully.")
                st.rerun()

        st.markdown("<hr class='nr-divider'>", unsafe_allow_html=True)
        _section("PASTE DOCUMENT TEXT")
        with st.expander("📋  Or paste document text directly"):
            paste_label = st.text_input("Document name", placeholder="e.g. Access Control Policy", key="nr_paste_lbl")
            paste_text  = st.text_area("Paste content", height=160, key="nr_paste_body",
                                       placeholder="Paste policy/SOP/control text here…")
            if st.button("Save Document", key="nr_save_paste"):
                if paste_label.strip() and paste_text.strip():
                    add_company_doc(paste_label.strip(), paste_text.strip())
                    st.success(f"✓  '{paste_label}' saved.")
                    st.rerun()
                else:
                    st.warning("Provide both a name and content.")

    with col_r:
        _section("SUGGESTED DOCUMENTS")
        st.markdown("<div class='nr-card blue'>", unsafe_allow_html=True)
        for doc in [
            "Information Security Policy",
            "Access Control Policy",
            "Data Privacy / DPDP Policy",
            "Incident Response Plan",
            "Business Continuity Plan",
            "IT Governance Policy",
            "Vendor Risk Policy",
            "Change Management SOP",
            "Internal Audit Report",
            "Existing Risk Register",
        ]:
            st.markdown(f"""
            <div style='font-size:13px;color:var(--text-secondary);padding:7px 0;
              border-bottom:1px solid var(--border-subtle);display:flex;
              gap:8px;align-items:center;'>
                <span style='color:var(--text-disabled);font-size:10px;'>○</span>{doc}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        co = get_company_docs()
        if co:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            _section("LOADED DOCUMENTS")
            for name in co:
                st.markdown(f"""
                <div style='font-size:12px;color:var(--success);padding:5px 0;
                  font-family:var(--font-mono);display:flex;align-items:center;gap:6px;'>
                    ✓ &nbsp;{name}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("🗑  Clear All Company Docs", key="nr_clear_docs", use_container_width=True):
                clear_company_docs()
                st.rerun()


def _page_gap():
    fw = get_frameworks()
    co = get_company_docs()

    _page_header(
        "Gap Analysis",
        "Gap <em>Analysis</em>",
        "Compare your documents against regulatory frameworks to surface missing requirements"
    )

    _fw_pills()

    if not co:
        st.markdown("""
        <div class='nr-alert warn'>
            <span class='nr-alert-icon'>⚠</span>
            <div>Upload your documents first → navigate to <b>Upload Documents</b></div>
        </div>
        """, unsafe_allow_html=True)
        return
    if not fw:
        st.markdown("""
        <div class='nr-alert danger'>
            <span class='nr-alert-icon'>⚠</span>
            <div>No framework PDFs found in <code>neurisk/documents/</code></div>
        </div>
        """, unsafe_allow_html=True)
        return

    col1, col2 = st.columns(2)
    with col1:
        selected_doc = st.selectbox("Your document to analyse", list(co.keys()), key="nr_gap_doc")
    with col2:
        selected_fw = st.multiselect(
            "Check against frameworks",
            list(fw.keys()),
            default=list(fw.keys()),
            key="nr_gap_fw",
        )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("🔍  Run Gap Analysis", type="primary", use_container_width=True, key="nr_run_gap"):
        if not selected_fw:
            st.warning("Select at least one framework.")
        else:
            st.markdown("<hr class='nr-divider'>", unsafe_allow_html=True)
            _section("ANALYSIS PROGRESS")

            progress_bar  = st.progress(0)
            status_text   = st.empty()
            results_accum = []
            total_fw      = len(selected_fw)

            for i, fw_name in enumerate(selected_fw):
                status_text.markdown(f"""
                <div class='nr-alert info' style='margin-bottom:0;'>
                    <span class='nr-alert-icon'>⬡</span>
                    <div>Analysing <b>{selected_doc}</b> against <b>{fw_name}</b>
                    &nbsp;·&nbsp; {i + 1} of {total_fw}</div>
                </div>
                """, unsafe_allow_html=True)
                fw_result = gap_analysis(selected_doc, [fw_name])
                if fw_result:
                    results_accum.extend(fw_result)
                progress_bar.progress((i + 1) / total_fw)

            status_text.markdown(f"""
            <div class='nr-alert ok'>
                <span class='nr-alert-icon'>✦</span>
                <div>Analysis complete — {total_fw} frameworks audited.</div>
            </div>
            """, unsafe_allow_html=True)

            if results_accum:
                st.session_state.nr_gap_results  = results_accum
                st.session_state.nr_gap_doc_name = selected_doc
            else:
                st.error("Could not parse any results. Check that framework PDFs are loaded and try again.")

    # ── Results ───────────────────────────────────────────────────────────────
    if "nr_gap_results" in st.session_state:
        results  = st.session_state.nr_gap_results
        doc_name = st.session_state.nr_gap_doc_name

        st.markdown("<hr class='nr-divider'>", unsafe_allow_html=True)
        _section(f"RESULTS — {doc_name.upper()}")

        full    = sum(1 for r in results if r.get("status") == "Full")
        partial = sum(1 for r in results if r.get("status") == "Partial")
        gap     = sum(1 for r in results if r.get("status") == "Gap")
        error   = sum(1 for r in results if r.get("status") == "Error")
        avg_cov = (
            round(sum(r.get("coverage_percent", 0) for r in results) / len(results))
            if results else 0
        )

        st.markdown(f"""
        <div class='nr-metrics'>
            <div class='nr-metric-card green'>
                <div class='nr-metric-icon'>✅</div>
                <div class='nr-metric-val green'>{full}</div>
                <div class='nr-metric-lbl'>Full Coverage</div>
                <div class='nr-metric-sub'>frameworks fully met</div>
            </div>
            <div class='nr-metric-card amber'>
                <div class='nr-metric-icon'>⚡</div>
                <div class='nr-metric-val amber'>{partial}</div>
                <div class='nr-metric-lbl'>Partial Coverage</div>
                <div class='nr-metric-sub'>gaps exist</div>
            </div>
            <div class='nr-metric-card red'>
                <div class='nr-metric-icon'>🚨</div>
                <div class='nr-metric-val red'>{gap}</div>
                <div class='nr-metric-lbl'>Gaps Identified</div>
                <div class='nr-metric-sub'>immediate action needed</div>
            </div>
            <div class='nr-metric-card cyan'>
                <div class='nr-metric-icon'>📊</div>
                <div class='nr-metric-val cyan'>{avg_cov}%</div>
                <div class='nr-metric-lbl'>Avg Coverage</div>
                <div class='nr-metric-sub'>across all frameworks</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if error:
            st.markdown(f"""
            <div class='nr-alert warn'>
                <span class='nr-alert-icon'>⚠</span>
                <div>{error} framework(s) failed to analyse. Check that their PDFs are loaded correctly.</div>
            </div>
            """, unsafe_allow_html=True)

        # Coverage bars
        _section("COVERAGE OVERVIEW")
        for r in sorted(results, key=lambda x: x.get("coverage_percent", 0)):
            pct    = r.get("coverage_percent", 0)
            status = r.get("status", "Gap")
            bc     = _bar_color(pct)
            tc     = _status_color(status)
            st.markdown(f"""
            <div class='nr-bar-wrap'>
                <div class='nr-bar-header'>
                    <span class='nr-bar-label'>{r.get("framework", "?")}</span>
                    <div class='nr-bar-meta'>
                        {_tag(status, tc)}
                        <span style='font-family:var(--font-mono);font-size:12px;
                          color:{bc};font-weight:500;'>{pct}%</span>
                    </div>
                </div>
                <div class='nr-bar-track'>
                    <div class='nr-bar-fill' style='width:{pct}%;background:{bc};'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Detailed findings
        st.markdown("<hr class='nr-divider'>", unsafe_allow_html=True)
        _section("DETAILED FINDINGS")

        sort_order = {"Gap": 0, "Partial": 1, "Full": 2, "Error": 3}
        sorted_results = sorted(results, key=lambda x: sort_order.get(x.get("status", "Error"), 3))

        for r in sorted_results:
            status  = r.get("status", "Gap")
            tc      = _status_color(status)
            matched = r.get("matched_requirements", [])
            gaps_l  = r.get("gaps", [])
            rec     = r.get("recommendation", "")
            pct     = r.get("coverage_percent", 0)
            fw_name = r.get("framework", "?")

            auto_expand = status in ("Gap", "Error")

            with st.expander(f"**{fw_name}** · {pct}% coverage", expanded=auto_expand):
                st.markdown(
                    f"{_tag(status, tc)}"
                    f"&nbsp;&nbsp;<span style='font-size:14px;font-weight:600;"
                    f"color:var(--text-primary);'>{fw_name}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                # Covered requirements
            if matched:
                st.markdown(
                    "<div class='nr-section-title' style='margin-top:4px;'>✓ &nbsp;COVERED REQUIREMENTS</div>",
                    unsafe_allow_html=True,
                )
                for m in matched:
                    if isinstance(m, dict):
                        clause   = m.get("clause", "")
                        location = m.get("location", "")
                        summary  = m.get("summary", "")
                        body = f"<b>{clause}</b>"
                        if summary:
                            body += f"<br>{summary}"
                        if location:
                            body += (f"<br><span style='font-family:var(--font-mono);"
                                    f"font-size:11px;color:var(--text-disabled);'>"
                                    f"📍 {location}</span>")
                    else:
                        body = str(m)
                    st.markdown(f"""
                    <div style='font-size:13px;color:var(--text-secondary);
                    padding:6px 0 6px 12px;
                    border-left:2px solid var(--success-border);
                    margin-bottom:5px;line-height:1.6;'>→ &nbsp;{body}</div>
                    """, unsafe_allow_html=True)
                # Missing requirements
                if gaps_l:
                    st.markdown(
                        "<div class='nr-section-title' style='margin-top:16px;'>⚠ &nbsp;MISSING REQUIREMENTS</div>",
                        unsafe_allow_html=True,
                    )
                    for g in gaps_l:
                        if isinstance(g, dict):
                            clause  = g.get("clause", "")
                            missing = g.get("what_is_missing", "")
                            why     = g.get("why_it_matters", "")
                            body = f"<b>{clause}</b>"
                            if missing:
                                body += f"<br>{missing}"
                            if why:
                                body += (f"<br><span style='color:var(--text-tertiary);"
                                        f"font-size:12px;'>Why it matters: {why}</span>")
                        else:
                            body = str(g)
                        st.markdown(f"""
                        <div style='font-size:13px;color:rgba(245,158,11,0.85);
                        padding:6px 0 6px 12px;
                        border-left:2px solid var(--warning-border);
                        margin-bottom:5px;line-height:1.6;'>! &nbsp;{body}</div>
                        """, unsafe_allow_html=True)
                # Recommendation
                if rec:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

                    if isinstance(rec, dict):
                        priority    = rec.get("priority", "Medium")
                        action      = rec.get("action", "")
                        timeline    = rec.get("timeline", "")
                        ref_section = rec.get("references_existing_section", "")

                        priority_color = {
                            "Critical": "red", "High": "amber",
                            "Medium": "blue",  "Low":  "green",
                        }.get(priority, "blue")

                        priority_icon = {
                            "Critical": "🔴", "High": "🟡",
                            "Medium":   "🔵", "Low":  "🟢",
                        }.get(priority, "🔵")

                        # Normalise action to lines
                        if isinstance(action, list):
                            raw_lines = action
                        else:
                            raw_lines = [
                                l.strip()
                                for l in action.replace("\\n", "\n").split("\n")
                                if l.strip()
                            ]

                        # Build action HTML
                        action_html = ""
                        for line in raw_lines:
                            m = re.match(r"^(\d+)\.\s+(.+)$", line, re.DOTALL)
                            if m:
                                num       = m.group(1)
                                remainder = m.group(2).strip()

                                colon_idx = remainder.find(": ")
                                if colon_idx != -1:
                                    header = remainder[:colon_idx].strip()
                                    body   = remainder[colon_idx + 2:].strip()
                                else:
                                    header = remainder
                                    body   = ""

                                sep_m = re.split(r"\s*[—–\-]\s*", header, maxsplit=1)
                                if len(sep_m) == 2:
                                    ref   = sep_m[0].strip()
                                    title = sep_m[1].strip()
                                else:
                                    ref   = ""
                                    title = header

                                action_html += f"""
                                <div style='display:flex;gap:12px;padding:12px 0;
                                  border-bottom:1px solid var(--border-subtle);'>
                                    <span style='font-family:var(--font-mono);
                                      font-size:11px;color:var(--text-disabled);
                                      min-width:18px;flex-shrink:0;padding-top:3px;
                                      font-weight:500;'>{num}.</span>
                                    <div style='flex:1;min-width:0;'>
                                        <div style='font-family:var(--font-mono);
                                          font-size:11px;font-weight:500;
                                          color:var(--warning);margin-bottom:4px;
                                          letter-spacing:0.2px;'>
                                            {'<span style="color:var(--text-tertiary);">' + ref + '</span> — ' if ref else ''}{title}
                                        </div>
                                        <div style='font-size:13px;
                                          color:var(--text-secondary);
                                          line-height:1.65;'>{body}</div>
                                    </div>
                                </div>"""
                            else:
                                action_html += f"""
                                <div style='font-size:13px;color:var(--text-secondary);
                                  padding:10px 0;border-bottom:1px solid var(--border-subtle);
                                  line-height:1.6;'>{line}</div>"""

                        st.markdown(f"""
                        <div class='nr-card {priority_color}' style='margin-top:4px;'>
                            <div style='display:flex;justify-content:space-between;
                              align-items:center;margin-bottom:14px;'>
                                <div class='nr-section-title'
                                  style='margin:0;padding:0;border:none;'>
                                    {priority_icon} &nbsp;RECOMMENDED ACTIONS
                                </div>
                                {_tag(priority, priority_color)}
                            </div>
                            <div>{action_html}</div>
                            <div style='display:flex;flex-wrap:wrap;gap:20px;
                              margin-top:14px;padding-top:12px;
                              border-top:1px solid var(--border-subtle);'>
                                <div style='display:flex;align-items:center;gap:6px;
                                  font-family:var(--font-mono);font-size:10px;
                                  color:var(--text-tertiary);'>
                                    <span>⏱</span>
                                    <span>TIMELINE</span>
                                    <span style='color:var(--text-secondary);font-weight:500;'>
                                        {timeline or "Not specified"}
                                    </span>
                                </div>
                                <div style='display:flex;align-items:center;gap:6px;
                                  font-family:var(--font-mono);font-size:10px;
                                  color:var(--text-tertiary);'>
                                    <span>📄</span>
                                    <span>UPDATE</span>
                                    <span style='color:var(--text-secondary);font-weight:500;'>
                                        {ref_section or "See policy"}
                                    </span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    else:
                        rec_lower = str(rec).lower()
                        if any(w in rec_lower for w in ["immediately", "critical", "urgent", "must"]):
                            p_color, p_label, p_icon = "red",   "Critical", "🔴"
                        elif any(w in rec_lower for w in ["high", "significant", "major"]):
                            p_color, p_label, p_icon = "amber", "High",     "🟡"
                        elif any(w in rec_lower for w in ["consider", "review", "low", "minor"]):
                            p_color, p_label, p_icon = "green", "Low",      "🟢"
                        else:
                            p_color, p_label, p_icon = "blue",  "Medium",   "🔵"

                        st.markdown(f"""
                        <div class='nr-card {p_color}' style='margin-top:4px;'>
                            <div style='display:flex;justify-content:space-between;
                              align-items:center;margin-bottom:8px;'>
                                <div class='nr-section-title'
                                  style='margin:0;padding:0;border:none;'>
                                    {p_icon} &nbsp;RECOMMENDED ACTION
                                </div>
                                {_tag(p_label, p_color)}
                            </div>
                            <div style='font-size:13px;color:var(--text-primary);
                              line-height:1.7;'>{rec}</div>
                        </div>
                        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if st.button("🗑  Clear Results", key="nr_clear_gap"):
            del st.session_state.nr_gap_results
            del st.session_state.nr_gap_doc_name
            st.rerun()


def _page_chat():
    fw = get_frameworks()
    co = get_company_docs()

    _page_header(
        "Compliance Chat",
        "Ask <em>Eva AI</em>",
        "Get AI-powered answers about your compliance posture, gaps, and required actions"
    )

    _fw_pills()

    if co:
        doc_pills = "".join(f"<span class='nr-pill on'>{d}</span>" for d in co)
        st.markdown(
            f"<div style='font-family:var(--font-mono);font-size:9px;"
            f"color:var(--text-disabled);letter-spacing:1.8px;text-transform:uppercase;"
            f"margin-bottom:6px;'>Your Documents</div>"
            f"<div class='nr-pills'>{doc_pills}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("""
        <div class='nr-alert warn'>
            <span class='nr-alert-icon'>⚠</span>
            <div>No company documents uploaded. Upload docs for personalised compliance answers.</div>
        </div>
        """, unsafe_allow_html=True)

    if "nr_chat" not in st.session_state:
        st.session_state.nr_chat = []

    # Chat history
    if st.session_state.nr_chat:
        st.markdown("<div class='nr-chat-wrap'>", unsafe_allow_html=True)
        for msg in st.session_state.nr_chat:
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='nr-bubble user'>"
                    f"<div class='nr-bubble-sender'>You</div>{msg['content']}</div>",
                    unsafe_allow_html=True
                )
            else:
                content = msg["content"].replace("\n", "<br>")
                st.markdown(
                    f"<div class='nr-bubble ai'>"
                    f"<div class='nr-bubble-sender'>⬡ Eva AI</div>{content}</div>",
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # Suggested questions
    if not st.session_state.nr_chat:
        _section("SUGGESTED QUESTIONS")
        suggestions = [
            "What are the top compliance gaps in our uploaded documents?",
            "Which DPDP Act requirements are we missing?",
            "How well does our security policy align with ISO 27001?",
            "What does RBI Master Direction require for incident reporting?",
            "Which controls from our documents satisfy NIST CSF?",
            "What are the highest risks based on our current policies?",
            "What actions should we take immediately based on Basel III gaps?",
            "Does our IT policy meet RBI AI Framework requirements?",
        ]
        st.markdown("<div class='nr-sug-grid'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for i, q in enumerate(suggestions):
            with (c1 if i % 2 == 0 else c2):
                if st.button(q, key=f"nr_sug_{i}", use_container_width=True):
                    st.session_state._nr_pending = q
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    question = st.chat_input("Ask about your compliance posture, gaps, risks…")

    if "_nr_pending" in st.session_state:
        question = st.session_state._nr_pending
        del st.session_state._nr_pending

    if question:
        st.session_state.nr_chat.append({"role": "user", "content": question})
        with st.spinner("Eva is analysing…"):
            answer = compliance_chat(question, st.session_state.nr_chat[:-1])
        st.session_state.nr_chat.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.nr_chat:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🗑  Clear Chat", key="nr_clear_chat"):
            st.session_state.nr_chat = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def render_neurisk_tab():
    """
    Called inside st.tab('NeuroRisk GRC').
    Handles its own sub-navigation via the sidebar.
    """
    _inject_nr_css()

    load_frameworks()

    if "nr_page" not in st.session_state:
        st.session_state.nr_page = "overview"

    _render_sidebar()

    st.markdown("<div class='neurisk-root'>", unsafe_allow_html=True)
    page = st.session_state.nr_page
    if   page == "overview": _page_overview()
    elif page == "upload":   _page_upload()
    elif page == "gap":      _page_gap()
    elif page == "chat":     _page_chat()
    st.markdown("</div>", unsafe_allow_html=True)