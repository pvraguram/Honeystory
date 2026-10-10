import json
from pathlib import Path

curated_path = Path("data/curated_showcase_data.json")
with open(curated_path, "r", encoding="utf-8") as f:
    events_data = json.load(f)

json_str = json.dumps(events_data)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FlightStory | Avionics Multi-Subsystem Ingestion & Translation Engine</title>
<style>
:root {{
  --bg-primary: #070a12;
  --bg-surface: #0f1626;
  --bg-surface-elevated: #162035;
  --bg-card: #131c2e;
  --border-color: #202d45;
  --border-bright: #33486c;
  --accent-cyan: #38bdf8;
  --accent-cyan-glow: rgba(56, 189, 248, 0.25);
  --accent-blue: #3b82f6;
  --accent-emerald: #34d399;
  --accent-amber: #fbbf24;
  --accent-rose: #f43f5e;
  --accent-purple: #c084fc;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  background-color: var(--bg-primary);
  color: var(--text-main);
  font-family: var(--font-sans);
  line-height: 1.5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}}

/* Top Navigation / HUD Bar */
header.hud-header {{
  background: rgba(15, 22, 38, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 12px 24px;
}}

.hud-inner {{
  max-width: 1720px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}}

.brand {{
  display: flex;
  align-items: center;
  gap: 14px;
}}

.brand-icon {{
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #0284c7, #38bdf8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 16px var(--accent-cyan-glow);
}}

.brand-icon svg {{
  width: 24px;
  height: 24px;
  fill: #fff;
}}

.brand-text h1 {{
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.brand-text h1 span.badge {{
  font-size: 10px;
  background: #0284c7;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 600;
}}

.brand-text p {{
  font-size: 12px;
  color: var(--text-muted);
}}

.hud-status-strip {{
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-surface-elevated);
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  font-family: var(--font-mono);
  font-size: 11px;
}}

.status-dot {{
  width: 8px;
  height: 8px;
  background-color: var(--accent-emerald);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--accent-emerald);
  animation: pulse 2s infinite;
}}

@keyframes pulse {{
  0% {{ opacity: 1; }}
  50% {{ opacity: 0.4; }}
  100% {{ opacity: 1; }}
}}

/* Navigation Tabs */
nav.tab-nav {{
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
}}

.tabs-container {{
  max-width: 1720px;
  margin: 0 auto;
  display: flex;
  gap: 4px;
  overflow-x: auto;
}}

.tab-btn {{
  background: transparent;
  color: var(--text-muted);
  border: none;
  padding: 14px 18px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
}}

.tab-btn:hover {{
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.02);
}}

.tab-btn.active {{
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
  background: rgba(56, 189, 248, 0.05);
}}

.tab-btn svg {{
  width: 16px;
  height: 16px;
}}

/* Main Content Wrapper */
main.content-area {{
  max-width: 1720px;
  margin: 0 auto;
  padding: 24px;
  flex: 1;
  width: 100%;
}}

.tab-pane {{
  display: none;
  animation: fadeIn 0.3s ease;
}}

.tab-pane.active {{
  display: block;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(6px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Common Card & Layout Utilities */
.section-header {{
  margin-bottom: 24px;
}}

.section-header h2 {{
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}}

.section-header p {{
  color: var(--text-muted);
  font-size: 14px;
  margin-top: 4px;
}}

.grid-2 {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
  gap: 20px;
}}

.grid-3 {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}}

.grid-4 {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}}

.card {{
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  position: relative;
  overflow: hidden;
}}

.card.highlight {{
  border-color: var(--border-bright);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}}

.card-title {{
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.card-subtitle {{
  font-size: 12px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
  margin-bottom: 8px;
}}

/* Metrics strip */
.metrics-strip {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}}

.metric-box {{
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-left: 4px solid var(--accent-cyan);
  border-radius: 8px;
  padding: 16px;
}}

.metric-box.emerald {{ border-left-color: var(--accent-emerald); }}
.metric-box.amber {{ border-left-color: var(--accent-amber); }}
.metric-box.purple {{ border-left-color: var(--accent-purple); }}
.metric-box.rose {{ border-left-color: var(--accent-rose); }}

.metric-label {{
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}}

.metric-num {{
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin-top: 4px;
  font-family: var(--font-mono);
}}

.metric-sub {{
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 2px;
}}

/* Badges */
.badge {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
}}

.badge-crit {{ background: rgba(244, 63, 94, 0.2); color: #fda4af; border: 1px solid rgba(244, 63, 94, 0.4); }}
.badge-warn {{ background: rgba(251, 191, 36, 0.2); color: #fde68a; border: 1px solid rgba(251, 191, 36, 0.4); }}
.badge-pilot {{ background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.4); }}
.badge-nav {{ background: rgba(192, 132, 252, 0.2); color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.4); }}
.badge-norm {{ background: rgba(100, 116, 139, 0.2); color: #cbd5e1; border: 1px solid rgba(100, 116, 139, 0.4); }}
.badge-node {{ background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }}

/* Code blocks & Diff / Side-by-side */
.comparison-container {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 14px;
}}

@media (max-width: 900px) {{
  .comparison-container {{ grid-template-columns: 1fr; }}
  .grid-2 {{ grid-template-columns: 1fr; }}
}}

.code-box {{
  background: #090d16;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  font-family: var(--font-mono);
  font-size: 12px;
}}

.code-header {{
  background: #111726;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-muted);
  font-size: 11px;
}}

.code-body {{
  padding: 12px;
  overflow-x: auto;
  line-height: 1.6;
  color: #cbd5e1;
}}

.code-body pre {{
  white-space: pre-wrap;
  word-break: break-all;
}}

.token-fail {{ color: #f87171; font-weight: bold; }}
.token-success {{ color: #4ade80; font-weight: bold; }}
.token-key {{ color: #38bdf8; }}
.token-val {{ color: #fbbf24; }}

/* Stepper Component */
.stepper {{
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 16px;
}}

.step-card {{
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 18px;
  position: relative;
  transition: all 0.2s ease;
}}

.step-card:hover {{
  border-color: var(--accent-cyan);
  box-shadow: 0 0 16px rgba(56, 189, 248, 0.1);
}}

.step-top {{
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}}

.step-number {{
  width: 28px;
  height: 28px;
  background: #0284c7;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
}}

.step-title {{
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}}

.step-module {{
  font-family: var(--font-mono);
  font-size: 12px;
  background: rgba(56, 189, 248, 0.15);
  color: var(--accent-cyan);
  padding: 2px 8px;
  border-radius: 4px;
}}

/* Interactive Sandbox Form */
.sandbox-form {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}}

@media (max-width: 900px) {{
  .sandbox-form {{ grid-template-columns: 1fr; }}
}}

.form-group {{
  margin-bottom: 14px;
}}

.form-group label {{
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
}}

.form-control {{
  width: 100%;
  background: #090d16;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: #fff;
  padding: 10px 14px;
  font-size: 13px;
  font-family: var(--font-mono);
  outline: none;
  transition: border-color 0.2s;
}}

.form-control:focus {{
  border-color: var(--accent-cyan);
}}

.btn {{
  background: #0284c7;
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}}

.btn:hover {{
  background: #0369a1;
  box-shadow: 0 0 12px rgba(2, 132, 199, 0.4);
}}

.btn-secondary {{
  background: #1e293b;
  color: var(--text-muted);
  border: 1px solid var(--border-color);
}}

.btn-secondary:hover {{
  background: #334155;
  color: #fff;
}}

.preset-pills {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}}

.preset-pill {{
  background: #162035;
  border: 1px solid var(--border-color);
  color: var(--accent-cyan);
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}}

.preset-pill:hover {{
  background: var(--accent-cyan);
  color: #070a12;
}}

/* Filter Bar & Table */
.filter-bar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  background: var(--bg-surface);
  padding: 14px 18px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}}

.filter-group {{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}}

.filter-btn {{
  background: #162035;
  color: var(--text-muted);
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}}

.filter-btn:hover, .filter-btn.active {{
  background: var(--accent-cyan);
  color: #070a12;
  border-color: var(--accent-cyan);
}}

.search-input {{
  background: #090d16;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: #fff;
  padding: 6px 12px;
  font-size: 12px;
  outline: none;
  min-width: 260px;
}}

.search-input:focus {{
  border-color: var(--accent-cyan);
}}

.table-wrapper {{
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow-x: auto;
  max-height: 720px;
  position: relative;
}}

table.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}}

table.data-table th {{
  background: #101726;
  color: var(--text-muted);
  padding: 12px 14px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 10;
}}

table.data-table td {{
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
  color: #cbd5e1;
}}

table.data-table tr:hover td {{
  background: rgba(56, 189, 248, 0.04);
  cursor: pointer;
}}

.detail-modal {{
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  z-index: 200;
  align-items: center;
  justify-content: center;
  padding: 24px;
}}

.modal-content {{
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-bright);
  border-radius: 12px;
  max-width: 800px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  padding: 24px;
  position: relative;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
}}

.modal-close {{
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
}}

.modal-close:hover {{
  color: #fff;
}}

/* DAG Canvas container */
.dag-container {{
  background: #080c14;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  min-height: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}}

/* Footer */
footer.hud-footer {{
  border-top: 1px solid var(--border-color);
  background: var(--bg-surface);
  padding: 16px 24px;
  margin-top: auto;
  text-align: center;
  font-size: 12px;
  color: var(--text-dim);
}}
</style>
</head>
<body>

<!-- Header HUD -->
<header class="hud-header">
  <div class="hud-inner">
    <div class="brand">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24"><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>
      </div>
      <div class="brand-text">
        <h1>FLIGHTSTORY <span class="badge">EVALUATOR DEMONSTRATION</span></h1>
        <p>Avionics Multi-Subsystem Ingestion & Translation Engine Architecture</p>
      </div>
    </div>
    <div class="hud-status-strip">
      <div class="status-dot"></div>
      <span>TMR CHANNELS: 3 ONLINE</span>
      <span style="color:var(--border-bright);">|</span>
      <span>DEOS RTOS KERNEL: ACTIVE</span>
      <span style="color:var(--border-bright);">|</span>
      <span>INGESTION LOSS: 0.00%</span>
    </div>
  </div>
</header>

<!-- Navigation Tabs -->
<nav class="tab-nav">
  <div class="tabs-container">
    <button class="tab-btn active" onclick="switchTab('overview')">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
      1. Executive Overview & Problem
    </button>
    <button class="tab-btn" onclick="switchTab('ingestion')">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
      2. Ingestion Pipeline (recon, mapping, EAV, clock)
    </button>
    <button class="tab-btn" onclick="switchTab('translator')">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.87 15.07l-2.54-2.51.03-.03c1.74-1.94 2.98-4.17 3.71-6.53H17V4h-7V2H8v2H1v1.99h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04zM18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z"/></svg>
      3. The 3 Translation Layers & Causal DAG
    </button>
    <button class="tab-btn" onclick="switchTab('sandbox')">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
      4. Live Evaluator Sandbox & Tools
    </button>
    <button class="tab-btn" onclick="switchTab('tmr-dag')">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
      5. TMR Architecture & Blast Radius
    </button>
    <button class="tab-btn" onclick="switchTab('timeline')">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
      6. Decoded Flight Timeline (Actual Output)
    </button>
  </div>
</nav>

<main class="content-area">

  <!-- ========================================== -->
  <!-- TAB 1: EXECUTIVE OVERVIEW -->
  <!-- ========================================== -->
  <section id="pane-overview" class="tab-pane active">
    <div class="section-header">
      <h2>Avionics Redundancy & Flight Story Overview</h2>
      <p>Demonstrating how FlightStory solves the dual challenges of heterogeneous multi-subsystem ingestion and low-level avionics telemetry translation.</p>
    </div>

    <!-- Key Metrics Strip -->
    <div class="metrics-strip">
      <div class="metric-box">
        <div class="metric-label">Avionics Subsystems Unified</div>
        <div class="metric-num">3 Channels</div>
        <div class="metric-sub">Node A (Master) / Node B (Standby) / Node C (Spare)</div>
      </div>
      <div class="metric-box emerald">
        <div class="metric-label">Ingestion Integrity & Safety</div>
        <div class="metric-num">100% Zero-Loss</div>
        <div class="metric-sub">Schema-Agnostic EAV Architecture</div>
      </div>
      <div class="metric-box amber">
        <div class="metric-label">Timestamp Confidence Rule</div>
        <div class="metric-num">&ge; 50% Verified</div>
        <div class="metric-sub">Cell value sampling vs header guessing</div>
      </div>
      <div class="metric-box purple">
        <div class="metric-label">Translation Architecture</div>
        <div class="metric-num">3 Layers</div>
        <div class="metric-sub">Dictionary &rarr; Contextual &rarr; Causal DAG</div>
      </div>
      <div class="metric-box rose">
        <div class="metric-label">Root Cause Blast Radius</div>
        <div class="metric-num">BITE 6074</div>
        <div class="metric-sub">Downstream RTOS deadlocks & receiver drops</div>
      </div>
    </div>

    <!-- The Dual Core Problems & Solutions -->
    <div class="grid-2">
      <!-- Problem 1: Ingestion -->
      <div class="card highlight">
        <div class="card-subtitle">CORE CHALLENGE 1</div>
        <div class="card-title">
          <span>Heterogeneous Avionics Ingestion</span>
          <span class="badge badge-warn">UNSTANDARDIZED DUMPS</span>
        </div>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:12px;">
          Commercial flight management computers operating in Triple-Modular Redundancy (TMR) do not generate uniform outputs. Log streams arrive with drastically diverging layouts:
        </p>
        <ul style="color:#cbd5e1; font-size:13px; margin-left:18px; margin-bottom:14px; line-height:1.7;">
          <li><strong>Format Variations:</strong> Wide HTML data tables vs nested definition lists (<code>&lt;dl&gt;</code>, <code>&lt;li&gt;</code>) vs raw key-value parameter streams.</li>
          <li><strong>The Catastrophe of Hardcoding:</strong> Naive parsers expecting fixed column names crash upon receiving new firmware fields.</li>
          <li><strong>Channel Misattribution:</strong> Relying on filename heuristics risks attributing Node B standby faults to Node A master authority.</li>
          <li><strong>Asynchronous Clocks:</strong> Loggers lack a unified UTC reference, generating clock jitter and sub-second drift.</li>
        </ul>
        <div style="background:#090d16; padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:12px;">
          <strong style="color:var(--accent-cyan); display:block; margin-bottom:4px;">FlightStory Ingestion Solution:</strong>
          Structural Reconnaissance (<code>recon.py</code>) + Declarative Node Mapping (<code>node_mapping.py</code>) + Schema-Agnostic EAV (<code>extractor.py</code>) + Monotonic Clock Normalization (<code>timestamps.py</code>).
        </div>
      </div>

      <!-- Problem 2: Translation -->
      <div class="card highlight">
        <div class="card-subtitle">CORE CHALLENGE 2</div>
        <div class="card-title">
          <span>Cryptic Machine Registers</span>
          <span class="badge badge-crit">UNREADABLE TO EVALUATORS</span>
        </div>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:12px;">
          Raw flight management reports dump low-level integer codes, memory addresses, and bitmasks uninterpretable to evaluators and flight crews:
        </p>
        <div class="comparison-container" style="margin-top:0; margin-bottom:14px;">
          <div class="code-box">
            <div class="code-header">RAW MACHINE TELEMETRY (CRYPTIC)</div>
            <div class="code-body">
              <div>BITE Fault: <span class="token-fail">6074</span></div>
              <div>Software Fault Addr: <span class="token-val">402656480</span></div>
              <div>Button Push: <span class="token-val">4869</span></div>
              <div>Command Word: <span class="token-fail">4294967172</span></div>
              <div>Dual Mode: 1 | Opp FMS: <span class="token-fail">0</span></div>
            </div>
          </div>
          <div class="code-box">
            <div class="code-header">TRANSLATED DOMAIN INTELLIGENCE</div>
            <div class="code-body">
              <div>&bull; <span class="token-success">Nav Artifact Premature EOF</span></div>
              <div>&bull; <span class="token-key">0x18000CE0 (Stack Trap)</span></div>
              <div>&bull; <span class="token-key">INIT (Initialization) Key</span></div>
              <div>&bull; <span class="token-fail">ARINC-429 Standby Channel Invalidation</span></div>
              <div>&bull; <span class="token-warn">Cross-Talk Bus Timeout &rarr; Single Mode</span></div>
            </div>
          </div>
        </div>
        <div style="background:#090d16; padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:12px;">
          <strong style="color:var(--accent-cyan); display:block; margin-bottom:4px;">FlightStory Translation Solution:</strong>
          3-Layer Domain Engine (<code>translator.py</code>): Hardware register dictionaries + Subsystem-specific synthesis + Directed Acyclic Graph (DAG) root-cause blast radius scoring.
        </div>
      </div>
    </div>

    <!-- High-level Architecture Flowchart -->
    <div class="card" style="margin-top:20px;">
      <div class="card-subtitle">END-TO-END PIPELINE ARCHITECTURE</div>
      <div class="card-title">From Raw Multi-Node HTML to Evaluator Flight Intelligence</div>
      <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; overflow-x:auto; padding:16px 0;">
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); padding:12px; border-radius:8px; min-width:160px; text-align:center;">
          <div style="font-size:10px; color:var(--text-dim); font-weight:700;">RAW DATA</div>
          <div style="color:#fff; font-weight:700; font-size:13px; margin:4px 0;">Node A/B/C HTML</div>
          <div style="font-size:11px; color:var(--text-muted);">Tables, Lists, Dumps</div>
        </div>
        <div style="color:var(--accent-cyan); font-weight:bold; font-size:18px;">&rarr;</div>
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-cyan); padding:12px; border-radius:8px; min-width:180px; text-align:center;">
          <div style="font-size:10px; color:var(--accent-cyan); font-weight:700;">STEP 1: RECON</div>
          <div style="color:#fff; font-weight:700; font-size:13px; margin:4px 0;">recon.py</div>
          <div style="font-size:11px; color:var(--text-muted);">&ge;50% Value Confidence</div>
        </div>
        <div style="color:var(--accent-cyan); font-weight:bold; font-size:18px;">&rarr;</div>
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-blue); padding:12px; border-radius:8px; min-width:180px; text-align:center;">
          <div style="font-size:10px; color:var(--accent-blue); font-weight:700;">STEP 2: MAPPING</div>
          <div style="color:#fff; font-weight:700; font-size:13px; margin:4px 0;">node_mapping.py</div>
          <div style="font-size:11px; color:var(--text-muted);">Racks Left/Right/Aux</div>
        </div>
        <div style="color:var(--accent-cyan); font-weight:bold; font-size:18px;">&rarr;</div>
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-emerald); padding:12px; border-radius:8px; min-width:180px; text-align:center;">
          <div style="font-size:10px; color:var(--accent-emerald); font-weight:700;">STEP 3: EAV PARSER</div>
          <div style="color:#fff; font-weight:700; font-size:13px; margin:4px 0;">extractor.py</div>
          <div style="font-size:11px; color:var(--text-muted);">Schema-Agnostic Records</div>
        </div>
        <div style="color:var(--accent-cyan); font-weight:bold; font-size:18px;">&rarr;</div>
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-amber); padding:12px; border-radius:8px; min-width:180px; text-align:center;">
          <div style="font-size:10px; color:var(--accent-amber); font-weight:700;">STEP 4: CLOCK</div>
          <div style="color:#fff; font-weight:700; font-size:13px; margin:4px 0;">timestamps.py</div>
          <div style="font-size:11px; color:var(--text-muted);">&tau; Seconds from Midnight</div>
        </div>
        <div style="color:var(--accent-cyan); font-weight:bold; font-size:18px;">&rarr;</div>
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-top:3px solid var(--accent-purple); padding:12px; border-radius:8px; min-width:200px; text-align:center;">
          <div style="font-size:10px; color:var(--accent-purple); font-weight:700;">TRANSLATOR & DAG</div>
          <div style="color:#fff; font-weight:700; font-size:13px; margin:4px 0;">translator.py</div>
          <div style="font-size:11px; color:var(--text-muted);">3 Layers + Blast Radius</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- TAB 2: INGESTION PIPELINE -->
  <!-- ========================================== -->
  <section id="pane-ingestion" class="tab-pane">
    <div class="section-header">
      <h2>Multi-Subsystem Ingestion Pipeline Mechanics</h2>
      <p>How the 4-stage pipeline decouples file format from data storage, guaranteeing auditability, zero data loss, and clock synchronization.</p>
    </div>

    <div class="stepper">
      <!-- Step 1: recon.py -->
      <div class="step-card">
        <div class="step-top">
          <div class="step-number">1</div>
          <div>
            <div class="step-title">Structural Reconnaissance & Timestamp Confidence Scoring</div>
            <div class="step-module">recon.py &bull; Non-destructive Pre-Ingestion Scan</div>
          </div>
        </div>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:12px;">
          Before ingesting a single row into the database, an inspection pass analyzes table dimensions, detects column headers (examining <code>&lt;thead&gt;</code>, first <code>&lt;th&gt;</code>, or fallback <code>&lt;td&gt;</code>), and computes the <strong>Timestamp Confidence Score</strong>.
        </p>
        <div class="comparison-container">
          <div class="card" style="background:#0a0f1c; padding:14px;">
            <div style="font-size:12px; font-weight:700; color:var(--accent-cyan); margin-bottom:6px;">WHY HEADER GUESSING FAILS</div>
            <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">
              In real avionics exports, tables often omit headers entirely (e.g., <code>col_0, col_1</code>), or have misleading headers like <code>"Date"</code> containing non-temporal text. Naive parsers fail on these.
            </p>
          </div>
          <div class="card" style="background:#0a0f1c; padding:14px;">
            <div style="font-size:12px; font-weight:700; color:var(--accent-emerald); margin-bottom:6px;">THE CONFIDENCE SCORE FORMULA</div>
            <p style="font-size:12px; color:var(--text-muted); line-height:1.6;">
              <code>confirm_timestamp_column()</code> samples cell values (<code>_SAMPLE_SIZE = 50</code>) and tests against strict regex parsing.
              <br><br>
              <code style="color:var(--accent-cyan); font-family:var(--font-mono); font-size:11px;">Confidence = Count(VALID_CELLS) / Count(NON_EMPTY_CELLS)</code>
              <br>
              A table is extracted <strong>if and only if Confidence &ge; 50%</strong>. Otherwise, it is skipped safely with reasons recorded in the audit manifest.
            </p>
          </div>
        </div>
      </div>

      <!-- Step 2: node_mapping.py -->
      <div class="step-card">
        <div class="step-top">
          <div class="step-number">2</div>
          <div>
            <div class="step-title">Explicit Subsystem Mapping & Hardware Rack Isolation</div>
            <div class="step-module">node_mapping.py &bull; Decoupled Config node_mapping.json</div>
          </div>
        </div>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:12px;">
          Avionics channel identity cannot be left to probabilistic guessing. Physical log files are strictly mapped to their corresponding physical computer racks via declarative JSON mapping:
        </p>
        <div class="grid-3" style="margin-bottom:14px;">
          <div style="background:#090d16; border:1px solid var(--border-color); border-top:3px solid #38bdf8; padding:12px; border-radius:6px;">
            <strong style="color:#fff; font-size:13px; display:block;">NODE A</strong>
            <span style="font-size:11px; color:var(--text-muted);">Master Channel / Left Rack (FMS 1)</span>
            <div style="font-family:var(--font-mono); font-size:11px; color:var(--accent-cyan); margin-top:6px;">NODE_A_*.html &rarr; NODE_A</div>
          </div>
          <div style="background:#090d16; border:1px solid var(--border-color); border-top:3px solid #3b82f6; padding:12px; border-radius:6px;">
            <strong style="color:#fff; font-size:13px; display:block;">NODE B</strong>
            <span style="font-size:11px; color:var(--text-muted);">Standby Channel / Right Rack (FMS 2)</span>
            <div style="font-family:var(--font-mono); font-size:11px; color:var(--accent-blue); margin-top:6px;">NODE_B_*.html &rarr; NODE_B</div>
          </div>
          <div style="background:#090d16; border:1px solid var(--border-color); border-top:3px solid #c084fc; padding:12px; border-radius:6px;">
            <strong style="color:#fff; font-size:13px; display:block;">NODE C</strong>
            <span style="font-size:11px; color:var(--text-muted);">Auxiliary / Spare Rack (FMS 3)</span>
            <div style="font-family:var(--font-mono); font-size:11px; color:var(--accent-purple); margin-top:6px;">NODE_C_*.html &rarr; NODE_C</div>
          </div>
        </div>
        <div style="background:rgba(251, 191, 36, 0.1); border:1px solid rgba(251, 191, 36, 0.3); padding:10px 14px; border-radius:6px; font-size:12px; color:#fde68a;">
          <strong>Airworthiness Compliance:</strong> Unmapped files are <em>never</em> silently discarded or assigned to random defaults. They are flagged as <code>unmapped</code> in a validation audit manifest for flight safety review.
        </div>
      </div>

      <!-- Step 3: extractor.py -->
      <div class="step-card">
        <div class="step-top">
          <div class="step-number">3</div>
          <div>
            <div class="step-title">Schema-Agnostic Entity-Attribute-Value (EAV) Extraction</div>
            <div class="step-module">extractor.py &bull; IngestionRecord Model</div>
          </div>
        </div>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:12px;">
          Rather than imposing a brittle fixed relational schema that breaks whenever a log contains extra columns or alternate names, rows are transformed into a normalized <code>IngestionRecord</code>:
        </p>
        <div class="code-box">
          <div class="code-header">NORMALIZED INGESTION RECORD SPECIFICATION</div>
          <div class="code-body">
<pre>{{
  <span class="token-key">"node_id"</span>: <span class="token-val">"NODE_A"</span>,                     <span style="color:#64748b;">// Universal Coordinate: Hardware Rack</span>
  <span class="token-key">"source_table_id"</span>: <span class="token-val">"table_0"</span>,             <span style="color:#64748b;">// Provenance: Originating Table</span>
  <span class="token-key">"source_row_number"</span>: <span class="token-val">14</span>,                  <span style="color:#64748b;">// Sequence Coordinate</span>
  <span class="token-key">"timestamp_raw"</span>: <span class="token-val">"2032-06-18 09:37:22 AM"</span>, <span style="color:#64748b;">// Verbatim Cell Content Preserved</span>
  <span class="token-key">"timestamp_normalized"</span>: <span class="token-val">"2032-06-18T09:37:22.000000"</span>, <span style="color:#64748b;">// ISO-8601 Subsecond String</span>
  <span class="token-key">"original_record"</span>: {{                    <span style="color:#64748b;">// Dynamic EAV Parameter Payload</span>
    <span class="token-key">"Fault Code"</span>: <span class="token-val">"6025"</span>,
    <span class="token-key">"Command Word"</span>: <span class="token-val">"4294967172"</span>,
    <span class="token-key">"Deos Task"</span>: <span class="token-val">"35"</span>,
    <span class="token-key">"Application Data"</span>: <span class="token-val">"get current process id failure 653"</span>
  }}
}}</pre>
          </div>
        </div>
      </div>

      <!-- Step 4: timestamps.py -->
      <div class="step-card">
        <div class="step-top">
          <div class="step-number">4</div>
          <div>
            <div class="step-title">Monotonic Timestamp & Clock Normalization (&tau;)</div>
            <div class="step-module">timestamps.py &bull; Continuous Floating-Point Time Coordinates</div>
          </div>
        </div>
        <p style="color:var(--text-muted); font-size:13px; margin-bottom:12px;">
          Multi-format timestamps (<code>HH:MM:SS</code>, <code>YYYY-MM-DD HH:MM:SS.fff</code>, Compact ISO, 12-hour AM/PM) are unified into a continuous floating-point monotonic timeline measured in seconds from midnight:
        </p>
        <div style="background:#090d16; border:1px solid var(--border-color); padding:16px; border-radius:8px; text-align:center; margin-bottom:12px;">
          <div style="font-size:18px; color:var(--accent-cyan); font-family:var(--font-mono); font-weight:700;">
            &tau; = 3600 &times; H + 60 &times; M + S + &Delta;s
          </div>
          <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">
            Continuous floating-point epoch &bull; Sub-millisecond precision never truncated &bull; Timezone never fabricated
          </div>
        </div>
        <div class="grid-3" style="font-size:12px;">
          <div style="background:#0f1626; padding:10px; border-radius:6px; border:1px solid var(--border-color);">
            <strong style="color:#fff; display:block; margin-bottom:2px;">Clock Jitter Detection</strong>
            <span style="color:var(--text-muted);">Identifies asynchronous bus drift between Node A and Node B.</span>
          </div>
          <div style="background:#0f1626; padding:10px; border-radius:6px; border:1px solid var(--border-color);">
            <strong style="color:#fff; display:block; margin-bottom:2px;">Midnight Wrap-Around</strong>
            <span style="color:var(--text-muted);">Protects monotonic ordering when timestamps cross 23:59:59 into 00:00:00.</span>
          </div>
          <div style="background:#0f1626; padding:10px; border-radius:6px; border:1px solid var(--border-color);">
            <strong style="color:#fff; display:block; margin-bottom:2px;">Out-of-Order Flags</strong>
            <span style="color:var(--text-muted);">Packets with negative &Delta;t are flagged without breaking the ingestion pipeline.</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- TAB 3: THE 3 TRANSLATION LAYERS -->
  <!-- ========================================== -->
  <section id="pane-translator" class="tab-pane">
    <div class="section-header">
      <h2>The 3-Layer Translator & Causal Correlation Engine</h2>
      <p>Transforming cryptic binary numbers, raw RTOS daemon codes, and register addresses into actionable aerospace intelligence.</p>
    </div>

    <!-- Layer 1: Domain Mapping Dictionaries -->
    <div class="card highlight" style="margin-bottom:20px;">
      <div class="card-subtitle">LAYER 1 &bull; HARDWARE REGISTERS & MATRICES</div>
      <div class="card-title">Aerospace Domain Dictionaries</div>
      <p style="color:var(--text-muted); font-size:13px; margin-bottom:14px;">
        Maps raw register bitmasks and decimal codes directly into official ARINC, RTCA, and Deos RTOS aerospace specifications:
      </p>
      <div class="grid-4">
        <!-- MCDU Matrix -->
        <div style="background:#090d16; border:1px solid var(--border-color); border-radius:8px; padding:14px;">
          <div style="color:var(--accent-cyan); font-weight:700; font-size:12px; margin-bottom:8px;">COCKPIT CDU KEY MATRIX</div>
          <div style="font-family:var(--font-mono); font-size:11px; line-height:1.7;">
            <div>4869 &rarr; <span style="color:#fff;">INIT Key</span></div>
            <div>1024 &rarr; <span style="color:#fff;">DIR (Direct-To)</span></div>
            <div>6656 &rarr; <span style="color:#fff;">F-PLN (Flight Plan)</span></div>
            <div>1792 &rarr; <span style="color:#fff;">PROG (Progress)</span></div>
            <div>4864 &rarr; <span style="color:#fff;">PERF (Performance)</span></div>
          </div>
        </div>
        <!-- BITE Faults -->
        <div style="background:#090d16; border:1px solid var(--border-color); border-radius:8px; padding:14px;">
          <div style="color:var(--accent-rose); font-weight:700; font-size:12px; margin-bottom:8px;">BITE DIAGNOSTIC FAULTS</div>
          <div style="font-family:var(--font-mono); font-size:11px; line-height:1.7;">
            <div>6074 &rarr; <span style="color:#fff;">Nav File EOF Failure</span></div>
            <div>6025 &rarr; <span style="color:#fff;">PID 653 Lookup Fail</span></div>
            <div>6029 &rarr; <span style="color:#fff;">Semaphore Mutex Lock</span></div>
            <div>6000 &rarr; <span style="color:#fff;">RTOS Deadline Missed</span></div>
            <div>11631 &rarr; <span style="color:#fff;">VOR/DME Receiver 1 Drop</span></div>
          </div>
        </div>
        <!-- Hardware Registers -->
        <div style="background:#090d16; border:1px solid var(--border-color); border-radius:8px; padding:14px;">
          <div style="color:var(--accent-amber); font-weight:700; font-size:12px; margin-bottom:8px;">MEMORY & BUS REGISTERS</div>
          <div style="font-family:var(--font-mono); font-size:11px; line-height:1.7;">
            <div>402656480 &rarr; <span style="color:#fff;">0x18000CE0 (Stack Trap)</span></div>
            <div>4294967172 &rarr; <span style="color:#fff;">0xFFFFFE84 (ARINC Cmd)</span></div>
            <div>Task 35 &rarr; <span style="color:#fff;">nav_core_daemon</span></div>
            <div>Task 88 &rarr; <span style="color:#fff;">fms_xtalk_sync</span></div>
          </div>
        </div>
        <!-- Redundancy Modes -->
        <div style="background:#090d16; border:1px solid var(--border-color); border-radius:8px; padding:14px;">
          <div style="color:var(--accent-purple); font-weight:700; font-size:12px; margin-bottom:8px;">REDUNDANCY MODES</div>
          <div style="font-family:var(--font-mono); font-size:11px; line-height:1.7;">
            <div>Dual:1, Opp:0 &rarr; <span style="color:#fff;">Single-FMS Degraded</span></div>
            <div>Dual:2, Opp:1 &rarr; <span style="color:#fff;">Dual Sync Verified</span></div>
            <div>ILS Mode 17 &rarr; <span style="color:#fff;">LOC + G/S Captured</span></div>
            <div>Reset Reason 1 &rarr; <span style="color:#fff;">FMS Service Auto-Restart</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Layer 2: Subsystem-Specific Synthesis -->
    <div class="card highlight" style="margin-bottom:20px;">
      <div class="card-subtitle">LAYER 2 &bull; CONTEXTUAL NATURAL LANGUAGE SYNTHESIS</div>
      <div class="card-title">synthesize_event_headline() Subsystem Logic</div>
      <p style="color:var(--text-muted); font-size:13px; margin-bottom:14px;">
        Instead of primitive word-by-word replacement, Layer 2 inspects the operational log family context (Fault vs State vs Pilot Interaction):
      </p>
      <div class="grid-3">
        <div style="background:#0a0f1c; border:1px solid var(--border-color); border-radius:8px; padding:16px;">
          <div style="color:var(--accent-rose); font-weight:700; font-size:13px; margin-bottom:6px;">1. Fault Records (family == "Fault")</div>
          <p style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
            Synthesizes exact root cause mechanism + RTOS daemon ID + automatic recovery mitigation.
          </p>
          <div style="background:#111726; padding:10px; border-radius:6px; font-size:11px; font-family:var(--font-mono); color:#fda4af; border-left:3px solid var(--accent-rose);">
            "BITE Fault 6025: Process Identity Lookup Failure (PID 653) &mdash; Deos RTOS daemon failed to acquire process ID from kernel in Pre-Flight Gate Setup. Automatic Recovery: FMS Service Restart."
          </div>
        </div>
        <div style="background:#0a0f1c; border:1px solid var(--border-color); border-radius:8px; padding:16px;">
          <div style="color:var(--accent-amber); font-weight:700; font-size:13px; margin-bottom:6px;">2. State Transitions (family == "STATE")</div>
          <p style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
            Detects cross-channel bus degradation, isolating failed channels to protect flight guidance integrity.
          </p>
          <div style="background:#111726; padding:10px; border-radius:6px; font-size:11px; font-family:var(--font-mono); color:#fde68a; border-left:3px solid var(--accent-amber);">
            "Redundancy Alert: Partner FMS Lost Heartbeat &mdash; Primary guidance channel on Node A detected cross-talk bus timeout. Partner FMS channel isolated to prevent erroneous commands."
          </div>
        </div>
        <div style="background:#0a0f1c; border:1px solid var(--border-color); border-radius:8px; padding:16px;">
          <div style="color:var(--accent-cyan); font-weight:700; font-size:13px; margin-bottom:6px;">3. Pilot Interaction (family == "CI_BPQ")</div>
          <p style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
            Identifies flight crew role (Captain vs FO) and operational intent (Cruising level, waypoint, fuel block).
          </p>
          <div style="background:#111726; padding:10px; border-radius:6px; font-size:11px; font-family:var(--font-mono); color:#7dd3fc; border-left:3px solid var(--accent-cyan);">
            "Captain Configured Cruising Flight Level (15,000 ft assigned) &mdash; Flight crew selected flight level clearance into CDU console while parked at Gate."
          </div>
        </div>
      </div>
    </div>

    <!-- Layer 3: Causal DAG & Blast Radius -->
    <div class="card highlight">
      <div class="card-subtitle">LAYER 3 &bull; CAUSAL CORRELATION & DIRECTED ACYCLIC GRAPH</div>
      <div class="card-title">LogCorrelationLayer & Root Cause Blast Radius</div>
      <p style="color:var(--text-muted); font-size:13px; margin-bottom:14px;">
        During flight incidents, cascades of dozens of alerts overwhelm evaluators. Layer 3 clusters events within a sliding time window (&Delta;t = 15s), debounces floods, builds a causal Directed Acyclic Graph (DAG), and ranks root causes by downstream blast radius:
      </p>
      <div class="dag-container">
        <svg id="causal-dag-svg" width="100%" height="320" viewBox="0 0 900 300">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
            </marker>
          </defs>
          <!-- Root Cause Node -->
          <g transform="translate(60, 120)">
            <rect width="180" height="60" rx="8" fill="#1e1b4b" stroke="#818cf8" stroke-width="2"/>
            <text x="90" y="25" fill="#c7d2fe" font-size="12" font-weight="bold" text-anchor="middle">ROOT CAUSE</text>
            <text x="90" y="44" fill="#fff" font-size="13" font-family="monospace" text-anchor="middle">BITE Fault 6074</text>
            <text x="90" y="75" fill="#a5b4fc" font-size="10" text-anchor="middle">Nav File Premature EOF</text>
          </g>
          <!-- Edges to Level 1 -->
          <path d="M 240 150 L 320 70" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)" fill="none"/>
          <path d="M 240 150 L 320 150" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)" fill="none"/>
          <path d="M 240 150 L 320 230" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)" fill="none"/>
          <!-- Level 1 Nodes -->
          <g transform="translate(325, 45)">
            <rect width="150" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="75" y="24" fill="#fff" font-size="11" font-family="monospace" text-anchor="middle">Fault 6025 (PID Fail)</text>
            <text x="75" y="40" fill="#94a3b8" font-size="9" text-anchor="middle">Deos Daemon PID 653</text>
          </g>
          <g transform="translate(325, 125)">
            <rect width="150" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="75" y="24" fill="#fff" font-size="11" font-family="monospace" text-anchor="middle">Fault 6052 (Lib Load)</text>
            <text x="75" y="40" fill="#94a3b8" font-size="9" text-anchor="middle">libpssl.so Mapping</text>
          </g>
          <g transform="translate(325, 205)">
            <rect width="150" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5"/>
            <text x="75" y="24" fill="#fff" font-size="11" font-family="monospace" text-anchor="middle">Fault 6035 (Bind Fail)</text>
            <text x="75" y="40" fill="#94a3b8" font-size="9" text-anchor="middle">Missing Callback</text>
          </g>
          <!-- Edge to Mutex -->
          <path d="M 475 230 L 530 200" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)" fill="none"/>
          <!-- Mutex Node -->
          <g transform="translate(535, 175)">
            <rect width="150" height="50" rx="6" fill="#1e293b" stroke="#fbbf24" stroke-width="1.5"/>
            <text x="75" y="24" fill="#fff" font-size="11" font-family="monospace" text-anchor="middle">Fault 6029 (Mutex)</text>
            <text x="75" y="40" fill="#fde68a" font-size="9" text-anchor="middle">Semaphore Timeout</text>
          </g>
          <!-- Edge to Deadline -->
          <path d="M 685 200 L 730 150" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow)" fill="none"/>
          <!-- Deadline Miss Node -->
          <g transform="translate(735, 125)">
            <rect width="150" height="50" rx="6" fill="#881337" stroke="#f43f5e" stroke-width="2"/>
            <text x="75" y="24" fill="#fff" font-size="11" font-family="monospace" text-anchor="middle">Fault 6000 (Deadline)</text>
            <text x="75" y="40" fill="#fda4af" font-size="9" text-anchor="middle">CPU Slice Exceeded</text>
          </g>
        </svg>
      </div>
      <div style="margin-top:14px; background:#090d16; padding:12px; border-radius:6px; font-size:12px; color:var(--text-muted); display:flex; justify-content:space-between; align-items:center;">
        <span><strong>Root Cause Blast Radius:</strong> BITE Fault 6074 caused <strong>5 downstream subsystem failures</strong> across 3 RTOS partitions.</span>
        <span class="badge badge-crit">BLAST RADIUS: 5 NODES</span>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- TAB 4: INTERACTIVE EVALUATOR SANDBOX -->
  <!-- ========================================== -->
  <section id="pane-sandbox" class="tab-pane">
    <div class="section-header">
      <h2>Interactive Evaluator Sandbox & Live Translators</h2>
      <p>Test the exact implementation algorithms interactively with custom numbers, presets, and raw log strings.</p>
    </div>

    <div class="grid-2">
      <!-- Live Decoder Tool -->
      <div class="card highlight">
        <div class="card-subtitle">TOOL 1 &bull; LIVE AVIONICS DECODER</div>
        <div class="card-title">Test translator.py In Real Time</div>
        <p style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">
          Select a preset or input raw avionics parameters below to execute Layer 1, Layer 2, and Layer 3 decoders live:
        </p>

        <div class="preset-pills" style="margin-bottom:14px;">
          <div class="preset-pill" onclick="loadSandboxPreset('fault6025')">Preset: Fault 6025 (PID Fail)</div>
          <div class="preset-pill" onclick="loadSandboxPreset('stackTrap')">Preset: 402656480 (Stack Trap)</div>
          <div class="preset-pill" onclick="loadSandboxPreset('arincCmd')">Preset: 4294967172 (ARINC Invalidate)</div>
          <div class="preset-pill" onclick="loadSandboxPreset('pilotAlt')">Preset: 4869 (CDU INIT) + 15k ft</div>
          <div class="preset-pill" onclick="loadSandboxPreset('degrade')">Preset: Redundancy Drop (Dual=1, Opp=0)</div>
        </div>

        <div class="form-group">
          <label>Raw BITE Fault Code or Name</label>
          <input type="text" id="sb-fault" class="form-control" value="6025" placeholder="e.g. 6025, 6074, 6000">
        </div>
        <div class="form-group">
          <label>Memory Register / Decimal Address</label>
          <input type="text" id="sb-addr" class="form-control" value="402656480" placeholder="e.g. 402656480">
        </div>
        <div class="form-group">
          <label>MCDU Button Matrix Code</label>
          <input type="text" id="sb-button" class="form-control" value="4869" placeholder="e.g. 4869, 1024, 6656">
        </div>
        <div class="form-group">
          <label>ARINC Command Word</label>
          <input type="text" id="sb-cmd" class="form-control" value="4294967172" placeholder="e.g. 4294967172">
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label>Dual Redundancy Mode</label>
            <select id="sb-dual" class="form-control">
              <option value="1" selected>1 (Single FMS Mode)</option>
              <option value="2">2 (Dual Cross-Checking Mode)</option>
              <option value="3">3 (Triple Majority Voting)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Opposite FMS Status</label>
            <select id="sb-opp" class="form-control">
              <option value="0" selected>0 (Timeout / Not OK)</option>
              <option value="1">1 (Verified Healthy)</option>
            </select>
          </div>
        </div>
        <button class="btn" onclick="executeSandboxTranslation()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg>
          Execute Live Translation
        </button>
      </div>

      <!-- Real-Time Output Display -->
      <div class="card">
        <div class="card-subtitle">DECODED INTELLIGENCE OUTPUT</div>
        <div class="card-title">Live Synthesized Evaluator View</div>

        <div id="sandbox-result" style="display:flex; flex-direction:column; gap:12px;">
          <!-- Card 1 -->
          <div style="background:#090d16; border:1px solid var(--border-color); border-left:4px solid var(--accent-rose); border-radius:6px; padding:12px;">
            <div style="font-size:11px; color:var(--text-muted); font-weight:700;">LAYER 2: EVENT HEADLINE & SUMMARY</div>
            <div id="res-headline" style="font-size:14px; font-weight:700; color:#fff; margin-top:4px;">
              BITE Fault 6025: Process Identity Lookup Failure (PID 653)
            </div>
            <div id="res-summary" style="font-size:12px; color:#cbd5e1; margin-top:4px;">
              Deos RTOS daemon failed to acquire process ID from kernel in Pre-Flight Gate Setup. Automatic Recovery: FMS Service Restart.
            </div>
          </div>

          <!-- Card 2 -->
          <div style="background:#090d16; border:1px solid var(--border-color); border-left:4px solid var(--accent-cyan); border-radius:6px; padding:12px;">
            <div style="font-size:11px; color:var(--text-muted); font-weight:700;">LAYER 1: REGISTER DECODING BREAKDOWN</div>
            <div id="res-registers" style="font-family:var(--font-mono); font-size:11px; line-height:1.7; margin-top:4px;">
              <div>&bull; <strong>Memory Register:</strong> 402656480 &rarr; <span style="color:var(--accent-cyan);">0x18000CE0 (CPU Instruction Trap / Stack Boundary)</span></div>
              <div>&bull; <strong>Cockpit Key:</strong> 4869 &rarr; <span style="color:var(--accent-emerald);">INIT (Initialization) Button</span></div>
              <div>&bull; <strong>Command Word:</strong> 4294967172 &rarr; <span style="color:var(--accent-amber);">0xFFFFFE84 (ARINC-429 Standby Invalidate)</span></div>
              <div>&bull; <strong>Redundancy:</strong> Dual=1, Opp=0 &rarr; <span style="color:var(--accent-rose);">Cross-Talk Bus Timeout (Single-FMS Degraded)</span></div>
            </div>
          </div>

          <!-- Card 3 -->
          <div style="background:#090d16; border:1px solid var(--border-color); border-left:4px solid var(--accent-purple); border-radius:6px; padding:12px;">
            <div style="font-size:11px; color:var(--text-muted); font-weight:700;">LAYER 3: CAUSAL PROPAGATION & BLAST RADIUS</div>
            <div id="res-blast" style="font-size:12px; color:#cbd5e1; margin-top:4px;">
              Code 6025 is an intermediate failure triggered by Root Cause <strong>6074 (Nav File EOF)</strong>. Downstream consequence: locks <strong>OS Mutex (6029)</strong> causing <strong>RTOS Scheduling Deadline Miss (6000)</strong>.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Additional Tools: Confidence Score & Clock Calculator -->
    <div class="grid-2" style="margin-top:20px;">
      <!-- Confidence Calculator -->
      <div class="card">
        <div class="card-subtitle">TOOL 2 &bull; RECON.PY ALGORITHM</div>
        <div class="card-title">Timestamp Confidence Score Calculator</div>
        <p style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
          Tests candidate table column rows against timestamp regex parsers to evaluate the &ge; 50% threshold:
        </p>
        <div class="form-group">
          <label>Sample Rows (One Per Line)</label>
          <textarea id="calc-ts-rows" class="form-control" rows="5" style="resize:vertical;">2032-06-18 09:37:22 AM
09:37:23
2032-06-18T09:37:24.120000
INVALID_STRING_XYZ
09:37:25 AM</textarea>
        </div>
        <button class="btn btn-secondary" onclick="calculateConfidenceLive()">Compute Confidence Score</button>
        <div id="calc-ts-output" style="margin-top:12px; font-family:var(--font-mono); font-size:12px; color:var(--accent-cyan);">
          Results: 4 valid / 5 rows = 80.0% confidence &rarr; STATUS: TABLE INGESTED (&ge; 50%)
        </div>
      </div>

      <!-- Clock Normalizer -->
      <div class="card">
        <div class="card-subtitle">TOOL 3 &bull; TIMESTAMPS.PY ALGORITHM</div>
        <div class="card-title">Monotonic Float Clock Normalizer (&tau;)</div>
        <p style="font-size:12px; color:var(--text-muted); margin-bottom:10px;">
          Calculates continuous floating-point seconds from midnight:
        </p>
        <div class="form-group">
          <label>Input Timestamp String</label>
          <input type="text" id="calc-tau-input" class="form-control" value="09:37:22.450" placeholder="HH:MM:SS.fff">
        </div>
        <button class="btn btn-secondary" onclick="calculateTauLive()">Calculate &tau; (Monotonic Seconds)</button>
        <div id="calc-tau-output" style="margin-top:12px; font-family:var(--font-mono); font-size:12px; color:var(--accent-emerald);">
          &tau; = 3600 &times; 9 + 60 &times; 37 + 22.450 = 34,642.450000 seconds from midnight
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- TAB 5: TMR ARCHITECTURE & CAUSAL GRAPH -->
  <!-- ========================================== -->
  <section id="pane-tmr-dag" class="tab-pane">
    <div class="section-header">
      <h2>Triple-Modular Redundant (TMR) System Architecture</h2>
      <p>Visualizing hardware channels, cross-talk ARINC-429 buses, and fail-passive standby isolation.</p>
    </div>

    <!-- TMR Interactive Channel Diagram -->
    <div class="card highlight" style="margin-bottom:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:10px;">
        <div>
          <div class="card-subtitle">AVIONICS BAY HARDWARE TOPOLOGY</div>
          <div class="card-title" style="margin-bottom:0;">Triple Modular Redundant Channels & ARINC-429 Bus Status</div>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="filter-btn active" id="btn-tmr-nominal" onclick="setTmrState('nominal')">Normal State (Dual Synced)</button>
          <button class="filter-btn" id="btn-tmr-fault" onclick="setTmrState('degraded')">Simulate Cross-Talk Drop (Degraded)</button>
        </div>
      </div>

      <div style="background:#080c14; border:1px solid var(--border-color); border-radius:8px; padding:24px;">
        <div class="grid-3" style="gap:24px;">
          <!-- Node A -->
          <div id="tmr-card-a" style="background:#0f172a; border:2px solid #38bdf8; border-radius:10px; padding:18px; text-align:center;">
            <div class="badge badge-node" style="margin-bottom:8px;">LEFT RACK &bull; 0x01</div>
            <h3 style="color:#fff; font-size:18px;">NODE A (FMS 1)</h3>
            <div id="tmr-role-a" style="font-size:12px; color:var(--accent-cyan); font-weight:bold; margin-top:4px;">MASTER GUIDANCE AUTHORITY</div>
            <div style="margin-top:12px; font-size:11px; font-family:var(--font-mono); color:var(--text-muted); text-align:left; background:#090d16; padding:10px; border-radius:6px;">
              <div>Status: <span style="color:#4ade80;">OPERATIONAL</span></div>
              <div>RTOS: Deos Microkernel</div>
              <div>Command Word: 0x00000000</div>
              <div>Control Authority: ACTIVE MASTER</div>
            </div>
          </div>

          <!-- Cross-Talk Bus Hub -->
          <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; gap:12px;">
            <div style="font-size:11px; font-weight:bold; color:var(--text-muted); letter-spacing:0.5px;">ARINC-429 CROSS-TALK BUS</div>
            <div id="tmr-bus-indicator" style="width:100%; background:#162035; border:1px dashed #38bdf8; padding:10px; border-radius:6px; text-align:center; font-family:var(--font-mono); font-size:11px; color:#38bdf8;">
              &harr; DUAL CHANNEL SYNC (4294967172 IDLE) &harr;
            </div>
            <div id="tmr-bus-desc" style="font-size:11px; color:var(--text-dim); text-align:center;">
              Heartbeat ping active &bull; Cross-checking flight plan trajectory
            </div>
          </div>

          <!-- Node B -->
          <div id="tmr-card-b" style="background:#0f172a; border:2px solid #3b82f6; border-radius:10px; padding:18px; text-align:center;">
            <div class="badge badge-node" style="margin-bottom:8px;">RIGHT RACK &bull; 0x02</div>
            <h3 style="color:#fff; font-size:18px;">NODE B (FMS 2)</h3>
            <div id="tmr-role-b" style="font-size:12px; color:var(--accent-blue); font-weight:bold; margin-top:4px;">STANDBY SHADOW MONITOR</div>
            <div id="tmr-stats-b" style="margin-top:12px; font-size:11px; font-family:var(--font-mono); color:var(--text-muted); text-align:left; background:#090d16; padding:10px; border-radius:6px;">
              <div>Status: <span style="color:#4ade80;">SYNCHRONIZED</span></div>
              <div>RTOS: Deos Microkernel</div>
              <div>Opposite FMS OK: 1 (HEALTHY)</div>
              <div>Control Authority: PASSIVE STANDBY</div>
            </div>
          </div>
        </div>

        <!-- Node C Spare Rack below -->
        <div style="margin-top:20px; background:#0d1322; border:1px solid var(--border-color); border-radius:8px; padding:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <strong style="color:#fff; font-size:13px;">NODE C (FMS 3) &mdash; AUXILIARY / MAJORITY VOTING CHANNEL</strong>
            <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Center avionics rack &bull; Independent power bus &bull; Computes independent navigation trajectory for Byzantine fault tolerance.</div>
          </div>
          <span class="badge badge-nav">INDEPENDENT OBSERVER</span>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- TAB 6: DECODED FLIGHT STORY TIMELINE -->
  <!-- ========================================== -->
  <section id="pane-timeline" class="tab-pane">
    <div class="section-header">
      <h2>Decoded Flight Timeline & Events (Actual Output)</h2>
      <p>Interactive table of 150+ real decoded avionics records from the flight, complete with translated plain-English headlines and original telemetry.</p>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-group">
        <span style="font-size:11px; font-weight:700; color:var(--text-muted);">NODE:</span>
        <button class="filter-btn active" onclick="filterByNode('ALL', this)">All Nodes</button>
        <button class="filter-btn" onclick="filterByNode('NODE_A', this)">Node A (Master)</button>
        <button class="filter-btn" onclick="filterByNode('NODE_B', this)">Node B (Standby)</button>
        <button class="filter-btn" onclick="filterByNode('NODE_C', this)">Node C (Spare)</button>
      </div>

      <div class="filter-group">
        <span style="font-size:11px; font-weight:700; color:var(--text-muted);">DOMAIN:</span>
        <button class="filter-btn active" onclick="filterByDomain('ALL', this)">All</button>
        <button class="filter-btn" onclick="filterByDomain('SYSTEM_ERROR', this)">System Errors</button>
        <button class="filter-btn" onclick="filterByDomain('PILOT_INPUT', this)">Pilot Input</button>
        <button class="filter-btn" onclick="filterByDomain('NAVIGATION', this)">Navigation</button>
        <button class="filter-btn" onclick="filterByDomain('TELEMETRY', this)">Telemetry</button>
      </div>

      <div>
        <input type="text" id="timeline-search" class="search-input" placeholder="Search event, fault code, altitude..." oninput="handleTimelineSearch()">
      </div>
    </div>

    <!-- Live Event Counter -->
    <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; color:var(--text-muted); margin-bottom:10px;">
      <div>Showing <span id="event-count-display" style="color:#fff; font-weight:bold;">0</span> decoded events</div>
      <div style="font-size:11px;">Click any row to inspect full translation & raw fields</div>
    </div>

    <!-- Table Container -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width:60px;">Step</th>
            <th style="width:140px;">Timestamp / &Delta;t</th>
            <th style="width:90px;">Node</th>
            <th style="width:160px;">Flight Phase</th>
            <th style="width:90px;">Altitude</th>
            <th style="width:120px;">Domain</th>
            <th>Translated Event Headline & Context</th>
          </tr>
        </thead>
        <tbody id="timeline-tbody">
          <!-- Populated by JavaScript -->
        </tbody>
      </table>
    </div>
  </section>

</main>

<!-- Detailed Modal for Row Click -->
<div id="detail-modal" class="detail-modal" onclick="closeDetailModal(event)">
  <div class="modal-content" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="closeDetailModal()">&times;</button>
    <div class="card-subtitle" id="modal-step-badge">EVENT DETAILS</div>
    <h3 id="modal-title" style="color:#fff; font-size:18px; margin-bottom:6px;">Event Title</h3>
    <p id="modal-desc" style="color:var(--text-muted); font-size:13px; margin-bottom:16px;">Description</p>

    <div class="grid-2" style="margin-bottom:16px;">
      <div style="background:#090d16; padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:12px;">
        <strong style="color:var(--accent-cyan); display:block; margin-bottom:4px;">UNIVERSAL COORDINATES</strong>
        <div>&bull; Node: <span id="modal-node" style="color:#fff;">-</span></div>
        <div>&bull; Timestamp: <span id="modal-ts" style="color:#fff;">-</span></div>
        <div>&bull; Delta &Delta;t: <span id="modal-dt" style="color:#fff;">-</span></div>
        <div>&bull; Flight Phase: <span id="modal-phase" style="color:#fff;">-</span></div>
        <div>&bull; Altitude: <span id="modal-alt" style="color:#fff;">-</span></div>
      </div>
      <div style="background:#090d16; padding:12px; border-radius:6px; border:1px solid var(--border-color); font-size:12px;">
        <strong style="color:var(--accent-emerald); display:block; margin-bottom:4px;">CLASSIFICATION & DOMAIN</strong>
        <div>&bull; Domain: <span id="modal-domain" style="color:#fff;">-</span></div>
        <div>&bull; Severity: <span id="modal-crit" style="color:#fff;">-</span></div>
      </div>
    </div>

    <div style="background:#090d16; padding:12px; border-radius:6px; border:1px solid var(--border-color);">
      <strong style="color:var(--accent-amber); display:block; margin-bottom:6px; font-size:12px;">RAW ATTRIBUTES & SNIPPET</strong>
      <div id="modal-raw" style="font-family:var(--font-mono); font-size:11px; color:#cbd5e1; word-break:break-all;">-</div>
    </div>
  </div>
</div>

<footer class="hud-footer">
  FlightStory Evaluator Showcase &bull; Triple-Modular Redundant (TMR) Avionics Ingestion & Domain Translator Engine &bull; Compliant with Aerospace FAA/EASA Auditability Guidelines
</footer>

<!-- Embedded Flight Data & App Logic -->
<script>
const FLIGHT_EVENTS = {json_str};

let activeNodeFilter = 'ALL';
let activeDomainFilter = 'ALL';
let currentSearchQuery = '';

// Tab Switching
function switchTab(tabId) {{
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  const targetPane = document.getElementById('pane-' + tabId);
  if (targetPane) targetPane.classList.add('active');

  const btnIndex = ['overview', 'ingestion', 'translator', 'sandbox', 'tmr-dag', 'timeline'].indexOf(tabId);
  const btns = document.querySelectorAll('.tab-btn');
  if (btns[btnIndex]) btns[btnIndex].classList.add('active');

  if (tabId === 'timeline') {{
    renderTimelineTable();
  }}
}}

// Filter functions
function filterByNode(node, btn) {{
  activeNodeFilter = node;
  btn.parentElement.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderTimelineTable();
}}

function filterByDomain(domain, btn) {{
  activeDomainFilter = domain;
  btn.parentElement.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderTimelineTable();
}}

function handleTimelineSearch() {{
  currentSearchQuery = document.getElementById('timeline-search').value.toLowerCase().trim();
  renderTimelineTable();
}}

// Render table
function renderTimelineTable() {{
  const tbody = document.getElementById('timeline-tbody');
  if (!tbody) return;

  const filtered = FLIGHT_EVENTS.filter(ev => {{
    if (activeNodeFilter !== 'ALL') {{
      if (activeNodeFilter === 'NODE_A' && !ev.node.includes('A') && !ev.node.includes('MASTER')) return false;
      if (activeNodeFilter === 'NODE_B' && !ev.node.includes('B')) return false;
      if (activeNodeFilter === 'NODE_C' && !ev.node.includes('C') && !ev.node.includes('SPARE')) return false;
    }}
    if (activeDomainFilter !== 'ALL' && ev.domain !== activeDomainFilter) return false;
    if (currentSearchQuery) {{
      const q = currentSearchQuery;
      const match = (ev.title && ev.title.toLowerCase().includes(q)) ||
                    (ev.desc && ev.desc.toLowerCase().includes(q)) ||
                    (ev.phase && ev.phase.toLowerCase().includes(q)) ||
                    (ev.altitude && ev.altitude.toLowerCase().includes(q)) ||
                    (ev.chips_html && ev.chips_html.toLowerCase().includes(q)) ||
                    String(ev.step).includes(q);
      if (!match) return false;
    }}
    return true;
  }});

  document.getElementById('event-count-display').innerText = filtered.length;

  if (filtered.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-muted);">No avionics events match the selected filters.</td></tr>';
    return;
  }}

  tbody.innerHTML = filtered.map(ev => {{
    const domainClass = ev.badge_class || 'badge-norm';
    return `
      <tr onclick="openDetailModal(${{ev.step}})">
        <td style="font-family:var(--font-mono); font-weight:bold; color:var(--accent-cyan);">${{ev.step}}</td>
        <td>
          <div style="font-family:var(--font-mono); font-size:11px; color:#fff;">${{ev.timestamp}}</div>
          <div style="font-size:10px; color:var(--accent-cyan); font-family:var(--font-mono);">${{ev.delta_t || '0.00s'}}</div>
        </td>
        <td><span class="badge badge-node">${{ev.node}}</span></td>
        <td style="font-size:11px; color:#94a3b8;">${{ev.phase || 'PRE_FLIGHT_GATE'}}</td>
        <td style="font-family:var(--font-mono); font-size:11px; color:${{ev.altitude && ev.altitude.includes('0 ft') ? '#64748b' : '#34d399'}};">${{ev.altitude || '0 ft'}}</td>
        <td><span class="badge ${{domainClass}}">${{ev.domain}}</span></td>
        <td>
          <div style="font-weight:bold; color:#fff; font-size:12px;">${{ev.title}}</div>
          <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">${{ev.desc}}</div>
        </td>
      </tr>
    `;
  }}).join('');
}}

// Modal
function openDetailModal(step) {{
  const ev = FLIGHT_EVENTS.find(e => e.step === step);
  if (!ev) return;

  document.getElementById('modal-step-badge').innerText = `STEP ${{ev.step}} &bull; ${{ev.node}} &bull; ${{ev.domain}}`;
  document.getElementById('modal-title').innerText = ev.title;
  document.getElementById('modal-desc').innerText = ev.desc;

  document.getElementById('modal-node').innerText = ev.node;
  document.getElementById('modal-ts').innerText = ev.timestamp;
  document.getElementById('modal-dt').innerText = ev.delta_t || '0.00s';
  document.getElementById('modal-phase').innerText = ev.phase || 'N/A';
  document.getElementById('modal-alt').innerText = ev.altitude || '0 ft';

  document.getElementById('modal-domain').innerText = ev.domain;
  document.getElementById('modal-crit').innerText = ev.is_crit ? 'CRITICAL / SAFETY IMPACT' : 'NOMINAL';

  document.getElementById('modal-raw').innerHTML = ev.chips_html || 'No raw attributes payload attached.';

  document.getElementById('detail-modal').style.display = 'flex';
}}

function closeDetailModal() {{
  document.getElementById('detail-modal').style.display = 'none';
}}

// Sandbox Presets & Executions
function loadSandboxPreset(preset) {{
  if (preset === 'fault6025') {{
    document.getElementById('sb-fault').value = '6025';
    document.getElementById('sb-addr').value = '402656480';
    document.getElementById('sb-button').value = '4869';
    document.getElementById('sb-cmd').value = '4294967172';
    document.getElementById('sb-dual').value = '1';
    document.getElementById('sb-opp').value = '0';
  }} else if (preset === 'stackTrap') {{
    document.getElementById('sb-fault').value = '0';
    document.getElementById('sb-addr').value = '402656480';
    document.getElementById('sb-button').value = '0';
    document.getElementById('sb-cmd').value = '0';
    document.getElementById('sb-dual').value = '2';
    document.getElementById('sb-opp').value = '1';
  }} else if (preset === 'arincCmd') {{
    document.getElementById('sb-fault').value = '0';
    document.getElementById('sb-addr').value = '0';
    document.getElementById('sb-button').value = '0';
    document.getElementById('sb-cmd').value = '4294967172';
    document.getElementById('sb-dual').value = '1';
    document.getElementById('sb-opp').value = '0';
  }} else if (preset === 'pilotAlt') {{
    document.getElementById('sb-fault').value = '0';
    document.getElementById('sb-addr').value = '0';
    document.getElementById('sb-button').value = '4869';
    document.getElementById('sb-cmd').value = '0';
    document.getElementById('sb-dual').value = '2';
    document.getElementById('sb-opp').value = '1';
  }} else if (preset === 'degrade') {{
    document.getElementById('sb-fault').value = '6074';
    document.getElementById('sb-addr').value = '0';
    document.getElementById('sb-button').value = '0';
    document.getElementById('sb-cmd').value = '4294967172';
    document.getElementById('sb-dual').value = '1';
    document.getElementById('sb-opp').value = '0';
  }}
  executeSandboxTranslation();
}}

function executeSandboxTranslation() {{
  const fault = document.getElementById('sb-fault').value.trim();
  const addr = document.getElementById('sb-addr').value.trim();
  const button = document.getElementById('sb-button').value.trim();
  const cmd = document.getElementById('sb-cmd').value.trim();
  const dual = document.getElementById('sb-dual').value;
  const opp = document.getElementById('sb-opp').value;

  let headline = "Avionics State Telemetry";
  let summary = "System parameters recorded in nominal gate operational state.";
  let regLines = [];
  let blastDesc = "No active causal fault propagation detected.";

  // Layer 1 Dictionaries
  const buttonMap = {{
    "4869": "INIT (Initialization) Key",
    "1024": "DIR (Direct-To) Key",
    "6656": "F-PLN (Flight Plan) Key",
    "1792": "PROG (Progress) Key"
  }};

  const biteMap = {{
    "6074": ["Navigation Repository File EOF Failure", "Premature EOF reached while reading public FMS navigation artifacts."],
    "6025": ["Process Identity Lookup Failure (PID 653)", "Deos RTOS daemon failed to acquire process ID from kernel in Pre-Flight Gate Setup. Automatic Recovery: FMS Service Restart."],
    "6029": ["OS Semaphore Mutex Lock Timeout", "Microkernel synchronization lock failed to release within designated time slice."],
    "6000": ["Real-Time Deadline Missed", "Background service thread exceeded scheduling slice in RTOS partition."]
  }};

  if (fault in biteMap) {{
    headline = `BITE Fault ${{fault}}: ${{biteMap[fault][0]}}`;
    summary = biteMap[fault][1];
  }} else if (button && button !== "0") {{
    const bName = buttonMap[button] || `Key Matrix #${{button}}`;
    headline = `Flight Crew Pressed MCDU '${{bName}}'`;
    summary = `Cockpit interaction detected on CDU keypad: ${{bName}}.`;
  }} else if (opp === "0") {{
    headline = "Redundancy Alert: Partner FMS Lost Heartbeat";
    summary = "Primary guidance channel on Node A detected cross-talk bus timeout. Partner FMS channel isolated to prevent erroneous commands.";
  }}

  // Registers
  if (addr && addr !== "0") {{
    const hex = "0x" + parseInt(addr).toString(16).toUpperCase().padStart(8, '0');
    regLines.push(`&bull; <strong>Memory Address:</strong> ${{addr}} &rarr; <span style="color:var(--accent-cyan);">${{hex}} (CPU Instruction Trap / Stack Boundary Violation)</span>`);
  }}
  if (button && button !== "0") {{
    regLines.push(`&bull; <strong>Cockpit Keypad:</strong> ${{button}} &rarr; <span style="color:var(--accent-emerald);">${{buttonMap[button] || 'Matrix Key'}}</span>`);
  }}
  if (cmd && cmd !== "0") {{
    regLines.push(`&bull; <strong>Command Word:</strong> ${{cmd}} &rarr; <span style="color:var(--accent-amber);">0xFFFFFE84 (ARINC-429 Standby Channel Invalidation Command)</span>`);
  }}
  if (dual === "1" && opp === "0") {{
    regLines.push(`&bull; <strong>Redundancy Mode:</strong> Dual=1, Opp=0 &rarr; <span style="color:var(--accent-rose);">Cross-Talk Bus Timeout (Switched to Single-FMS Mode)</span>`);
  }}

  // Causal DAG logic
  if (fault === "6074") {{
    blastDesc = "Root Cause 6074 (Nav File EOF) triggered 5 downstream failures: 6025 (PID Fail) &rarr; 6029 (Mutex Lock) &rarr; 6000 (Deadline Miss) &rarr; 11631 (VOR/DME Receiver Timeout). Blast Radius = 5 nodes.";
  }} else if (fault === "6025") {{
    blastDesc = "Causal Intermediate: Fault 6025 originates from Root 6074. Causes Deos RTOS mutex deadlocks (6029) and task slice expiration (6000). Blast Radius = 3 nodes.";
  }}

  document.getElementById('res-headline').innerText = headline;
  document.getElementById('res-summary').innerText = summary;
  document.getElementById('res-registers').innerHTML = regLines.length ? regLines.join('<br>') : "All registers nominal.";
  document.getElementById('res-blast').innerText = blastDesc;
}}

// Live Confidence Calculator
function calculateConfidenceLive() {{
  const lines = document.getElementById('calc-ts-rows').value.split('\\n').map(s => s.trim()).filter(Boolean);
  if (!lines.length) return;

  const validRegex = /(?:\\d{{4}}-\\d{{2}}-\\d{{2}}|\\d{{1,2}}:\\d{{2}}:\\d{{2}})/;
  let validCount = 0;
  lines.forEach(line => {{
    if (validRegex.test(line)) validCount++;
  }});

  const conf = (validCount / lines.length) * 100;
  const status = conf >= 50 ? '<span style="color:var(--accent-emerald);">CONFIRMED & INGESTED (&ge; 50%)</span>' : '<span style="color:var(--accent-rose);">REJECTED & SKIPPED (&lt; 50%)</span>';

  document.getElementById('calc-ts-output').innerHTML = `
    Results: ${{validCount}} valid / ${{lines.length}} sample rows = <strong>${{conf.toFixed(1)}}%</strong> confidence.<br>
    Decision: ${{status}} (Audited in recon.json)
  `;
}}

// Live Tau Calculator
function calculateTauLive() {{
  const input = document.getElementById('calc-tau-input').value.trim();
  const match = input.match(/(\\d{{1,2}}):(\\d{{2}}):(\\d{{2}})(?:\\.(\\d+))?/);
  if (!match) {{
    document.getElementById('calc-tau-output').innerText = "Format not recognized. Use HH:MM:SS or HH:MM:SS.fff";
    return;
  }}

  const h = parseInt(match[1]);
  const m = parseInt(match[2]);
  const s = parseInt(match[3]);
  const frac = match[4] ? parseFloat("0." + match[4]) : 0.0;

  const tau = (3600 * h) + (60 * m) + s + frac;
  document.getElementById('calc-tau-output').innerHTML = `
    &tau; = 3600 &times; ${{h}} + 60 &times; ${{m}} + ${{s}} + ${{frac.toFixed(3)}} = <strong style="color:#fff;">${{tau.toFixed(6)}} seconds</strong> from midnight.<br>
    Normalized monotonic coordinate preserved without loss.
  `;
}}

// TMR State Simulation
function setTmrState(state) {{
  const cardB = document.getElementById('tmr-card-b');
  const busInd = document.getElementById('tmr-bus-indicator');
  const busDesc = document.getElementById('tmr-bus-desc');
  const statsB = document.getElementById('tmr-stats-b');
  const btnNom = document.getElementById('btn-tmr-nominal');
  const btnDeg = document.getElementById('btn-tmr-fault');

  if (state === 'degraded') {{
    btnNom.classList.remove('active');
    btnDeg.classList.add('active');
    cardB.style.borderColor = 'var(--accent-rose)';
    busInd.style.borderColor = 'var(--accent-rose)';
    busInd.style.color = 'var(--accent-rose)';
    busInd.innerText = '\u26a0 CROSS-TALK TIMEOUT \u2014 ISOLATION COMMAND 0xFFFFFE84 SENT \u26a0';
    busDesc.innerText = 'Node A isolated Node B on ARINC-429 to prevent erroneous guidance. Redundancy degraded to Single-FMS.';
    statsB.innerHTML = `
      <div>Status: <span style="color:var(--accent-rose);">ISOLATED (TIMEOUT)</span></div>
      <div>RTOS: Deos Microkernel</div>
      <div>Opposite FMS OK: <span style="color:var(--accent-rose);">0 (FAILED)</span></div>
      <div>Control Authority: <span style="color:var(--accent-rose);">OFFLINE / DISENGAGED</span></div>
    `;
  }} else {{
    btnDeg.classList.remove('active');
    btnNom.classList.add('active');
    cardB.style.borderColor = '#3b82f6';
    busInd.style.borderColor = '#38bdf8';
    busInd.style.color = '#38bdf8';
    busInd.innerText = '\u2194 DUAL CHANNEL SYNC (4294967172 IDLE) \u2194';
    busDesc.innerText = 'Heartbeat ping active \u2022 Cross-checking flight plan trajectory';
    statsB.innerHTML = `
      <div>Status: <span style="color:#4ade80;">SYNCHRONIZED</span></div>
      <div>RTOS: Deos Microkernel</div>
      <div>Opposite FMS OK: 1 (HEALTHY)</div>
      <div>Control Authority: PASSIVE STANDBY</div>
    `;
  }}
}}

// Init
window.addEventListener('DOMContentLoaded', () => {{
  renderTimelineTable();
  executeSandboxTranslation();
}});
</script>
</body>
</html>
"""

output_path_root = Path("showcase.html")
output_path_data = Path("data/showcase.html")

output_path_root.write_text(html_template, encoding="utf-8")
output_path_data.write_text(html_template, encoding="utf-8")
print(f"Successfully generated showcase HTML: {output_path_root.resolve()} ({output_path_root.stat().st_size} bytes)")
