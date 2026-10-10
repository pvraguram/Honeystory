import json
from pathlib import Path

curated_path = Path("data/curated_showcase_data.json")
with open(curated_path, "r", encoding="utf-8") as f:
    events_data = json.load(f)

json_str = json.dumps(events_data)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FlightStory | Avionics Architecture & Visual Engine</title>
<style>
:root {{
  --bg-dark: #060911;
  --bg-card: #0c1220;
  --bg-card-hover: #121b30;
  --border: #1c2842;
  --border-glow: #2d416b;
  --cyan: #38bdf8;
  --cyan-glow: rgba(56, 189, 248, 0.3);
  --blue: #3b82f6;
  --emerald: #10b981;
  --amber: #f59e0b;
  --rose: #f43f5e;
  --purple: #a855f7;
  --indigo: #6366f1;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

body {{
  background: var(--bg-dark);
  color: var(--text);
  font-family: var(--font-sans);
  overflow-x: hidden;
  user-select: none;
}}

/* Header HUD Bar */
header.hud {{
  background: rgba(12, 18, 32, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.hud-brand {{
  display: flex;
  align-items: center;
  gap: 12px;
}}

.hud-logo {{
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #0284c7, #38bdf8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 16px var(--cyan-glow);
}}

.hud-title {{
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 1px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.hud-badge {{
  font-size: 10px;
  background: #0284c7;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
}}

.hud-status {{
  display: flex;
  align-items: center;
  gap: 16px;
  font-family: var(--font-mono);
  font-size: 11px;
  background: #080d18;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
}}

.hud-led {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--emerald);
  box-shadow: 0 0 8px var(--emerald);
  animation: pulse 1.5s infinite;
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.3; }}
}}

/* Tab Switcher */
nav.tab-bar {{
  background: #090e1a;
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  display: flex;
  gap: 6px;
  overflow-x: auto;
}}

.tab-btn {{
  background: transparent;
  color: var(--text-muted);
  border: none;
  padding: 14px 20px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
}}

.tab-btn:hover {{
  color: #fff;
  background: rgba(255, 255, 255, 0.02);
}}

.tab-btn.active {{
  color: var(--cyan);
  border-bottom-color: var(--cyan);
  background: rgba(56, 189, 248, 0.06);
}}

.tab-btn svg {{
  width: 16px;
  height: 16px;
}}

/* Main Workspace */
main.viewport {{
  padding: 24px;
  max-width: 1720px;
  margin: 0 auto;
}}

.tab-pane {{
  display: none;
}}

.tab-pane.active {{
  display: block;
  animation: fadeIn 0.25s ease-out;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(4px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Visual Canvas & Flowchart Cards */
.canvas-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  margin-bottom: 24px;
}}

.canvas-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}}

.canvas-title {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
  color: var(--cyan);
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 8px;
}}

.canvas-tools {{
  display: flex;
  gap: 8px;
}}

.tool-pill {{
  background: #080d18;
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
}}

.tool-pill:hover, .tool-pill.active {{
  background: var(--cyan);
  color: #060911;
  border-color: var(--cyan);
  font-weight: bold;
}}

/* SVG Diagrams Styling */
svg.diagram {{
  width: 100%;
  height: auto;
  display: block;
}}

.flow-node {{
  cursor: pointer;
  transition: all 0.2s;
}}

.flow-node:hover rect, .flow-node:hover polygon {{
  stroke: var(--cyan);
  stroke-width: 2.5px;
  filter: drop-shadow(0 0 10px var(--cyan-glow));
}}

.flow-line {{
  stroke: var(--border-glow);
  stroke-width: 2;
  fill: none;
}}

.flow-line-active {{
  stroke: var(--cyan);
  stroke-width: 2.5;
  stroke-dasharray: 6 4;
  animation: dash 1s linear infinite;
  fill: none;
}}

@keyframes dash {{
  to {{ stroke-dashoffset: -20; }}
}}

/* Inspector Tray */
.inspector-tray {{
  background: #080d18;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 18px;
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 12px;
}}

.inspector-meta {{
  display: flex;
  gap: 20px;
}}

.meta-chip {{
  display: flex;
  align-items: center;
  gap: 6px;
}}

.meta-chip span.label {{
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
}}

.meta-chip span.val {{
  color: #fff;
  font-weight: bold;
}}

/* Interactive Scrubber */
.scrubber-bar {{
  display: flex;
  align-items: center;
  gap: 16px;
  background: #080d18;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 18px;
  margin-top: 14px;
}}

.scrubber-slider {{
  flex: 1;
  -webkit-appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #1c2842;
  outline: none;
}}

.scrubber-slider::-webkit-slider-thumb {{
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 10px var(--cyan);
  cursor: pointer;
}}

/* Avionics PFD Dashboard HUD */
.pfd-grid {{
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 16px;
}}

@media (max-width: 1024px) {{
  .pfd-grid {{ grid-template-columns: 1fr; }}
}}

.gauge-panel {{
  background: #080d18;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  position: relative;
}}

.gauge-label {{
  position: absolute;
  top: 10px;
  left: 12px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 700;
}}

.pfd-horizon {{
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 3px solid var(--cyan);
  overflow: hidden;
  position: relative;
  background: linear-gradient(to bottom, #0284c7 0%, #0284c7 50%, #854d0e 50%, #854d0e 100%);
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
}}

.pfd-crosshair {{
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 4px;
  background: #fbbf24;
  box-shadow: 0 0 8px #fbbf24;
}}

.pfd-crosshair::after {{
  content: '';
  position: absolute;
  left: 50%;
  top: -12px;
  transform: translateX(-50%);
  width: 4px;
  height: 12px;
  background: #fbbf24;
}}

.tape-box {{
  font-family: var(--font-mono);
  text-align: center;
}}

.tape-val {{
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  letter-spacing: 1px;
}}

.tape-unit {{
  font-size: 11px;
  color: var(--cyan);
  font-weight: 700;
}}

/* Mini Sparkline / Step indicators */
.step-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}}

.step-box {{
  background: #080d18;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
}}

.step-box:hover, .step-box.active {{
  border-color: var(--cyan);
  box-shadow: 0 0 16px var(--cyan-glow);
}}

.step-badge {{
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--cyan);
  background: rgba(56, 189, 248, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 8px;
}}

.step-head {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}}

.step-svg-icon {{
  width: 100%;
  height: 80px;
  margin-top: 8px;
}}
</style>
</head>
<body>

<!-- HUD Top Strip -->
<header class="hud">
  <div class="hud-brand">
    <div class="hud-logo">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="#fff"><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>
    </div>
    <div class="hud-title">
      FLIGHTSTORY <span class="hud-badge">VISUAL ARCHITECTURE</span>
    </div>
  </div>
  <div class="hud-status">
    <div class="hud-led"></div>
    <span>TMR: 3 CHANNELS</span>
    <span style="color:#334155;">|</span>
    <span>ARINC-429: PASSIVE RX</span>
    <span style="color:#334155;">|</span>
    <span>MODE: ZERO LOSS</span>
  </div>
</header>

<!-- Visual Navigation Tabs -->
<nav class="tab-bar">
  <button class="tab-btn active" onclick="showTab('ingestion')">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
    1. DATA INGESTION PIPELINE
  </button>
  <button class="tab-btn" onclick="showTab('translation')">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.87 15.07l-2.54-2.51.03-.03c1.74-1.94 2.98-4.17 3.71-6.53H17V4h-7V2H8v2H1v1.99h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04zM18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z"/></svg>
    2. DATA TRANSLATION ARCHITECTURE
  </button>
  <button class="tab-btn" onclick="showTab('correlation')">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
    3. DATA CORRELATION & CAUSAL DAG
  </button>
  <button class="tab-btn" onclick="showTab('flightstory')">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
    4. FLIGHT STORY MISSION PROFILE
  </button>
  <button class="tab-btn" onclick="showTab('visualization')">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
    5. AVIONICS TMR & COCKPIT VISUALIZATION
  </button>
</nav>

<main class="viewport">

  <!-- ==================================================== -->
  <!-- TAB 1: DATA INGESTION PIPELINE (FLOWCHARTS) -->
  <!-- ==================================================== -->
  <section id="pane-ingestion" class="tab-pane active">
    <div class="canvas-card">
      <div class="canvas-header">
        <div class="canvas-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M4 18h16c.55 0 1-.45 1-1s-.45-1-1-1H4c-.55 0-1 .45-1 1s.45 1 1 1zm0-5h16c.55 0 1-.45 1-1s-.45-1-1-1H4c-.55 0-1 .45-1 1s.45 1 1 1zM3 7c0 .55.45 1 1 1h16c.55 0 1-.45 1-1s-.45-1-1-1H4c-.55 0-1 .45-1 1z"/></svg>
          MULTI-SUBSYSTEM INGESTION ARCHITECTURE & FLOWCHART
        </div>
        <div class="canvas-tools">
          <div class="tool-pill active" onclick="highlightIngestionStep('all')">COMPLETE FLOW</div>
          <div class="tool-pill" onclick="highlightIngestionStep('recon')">1. RECON</div>
          <div class="tool-pill" onclick="highlightIngestionStep('mapping')">2. MAPPING</div>
          <div class="tool-pill" onclick="highlightIngestionStep('eav')">3. EAV</div>
          <div class="tool-pill" onclick="highlightIngestionStep('clock')">4. CLOCK</div>
        </div>
      </div>

      <!-- Main Ingestion Flowchart SVG -->
      <svg id="svg-ingestion-flow" class="diagram" viewBox="0 0 1400 480">
        <defs>
          <linearGradient id="grad-cyan" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#0284c7"/>
            <stop offset="100%" stop-color="#38bdf8"/>
          </linearGradient>
          <linearGradient id="grad-dark" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#0f172a"/>
            <stop offset="100%" stop-color="#1e293b"/>
          </linearGradient>
          <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8"/>
          </marker>
          <marker id="arrow-rose" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e"/>
          </marker>
          <marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981"/>
          </marker>
        </defs>

        <!-- INPUT SOURCES (Column 1) -->
        <g id="grp-inputs" class="flow-node" onclick="setIngestionInfo('HETEROGENEOUS INPUTS', 'Wide HTML Tables + Nested <dl>/<li> + KV Streams', 'Unstandardized avionics log structures across channels.')">
          <rect x="30" y="50" width="160" height="60" rx="8" fill="url(#grad-dark)" stroke="#334155" stroke-width="1.5"/>
          <text x="110" y="78" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">SOURCE LOG 1</text>
          <text x="110" y="96" fill="#fff" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">&lt;table&gt; Wide Grid</text>

          <rect x="30" y="140" width="160" height="60" rx="8" fill="url(#grad-dark)" stroke="#334155" stroke-width="1.5"/>
          <text x="110" y="168" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">SOURCE LOG 2</text>
          <text x="110" y="186" fill="#fff" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">&lt;dl&gt; &lt;li&gt; Nested</text>

          <rect x="30" y="230" width="160" height="60" rx="8" fill="url(#grad-dark)" stroke="#334155" stroke-width="1.5"/>
          <text x="110" y="258" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">SOURCE LOG 3</text>
          <text x="110" y="276" fill="#fff" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">Key-Value Stream</text>
        </g>

        <!-- Connectors to STEP 1 -->
        <path d="M 190 80 L 260 170" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 190 170 L 260 170" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 190 260 L 260 170" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- STEP 1: recon.py -->
        <g id="grp-recon" class="flow-node" onclick="setIngestionInfo('STEP 1: recon.py', 'Cell Value Regex Profiler (_SAMPLE_SIZE=50)', 'Calculates Confidence Score = Valid_TS / Non_Empty. Ignores misleading header names.')">
          <rect x="265" y="120" width="190" height="100" rx="10" fill="#0f172a" stroke="#38bdf8" stroke-width="2"/>
          <rect x="275" y="130" width="80" height="18" rx="4" fill="#0284c7"/>
          <text x="315" y="143" fill="#fff" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">STEP 1</text>
          <text x="360" y="165" fill="#38bdf8" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">recon.py</text>
          <text x="360" y="185" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">Value Regex Test</text>
          <text x="360" y="202" fill="#38bdf8" font-size="10" font-family="monospace" text-anchor="middle">_SAMPLE_SIZE = 50</text>
        </g>

        <!-- Connector to Decision Diamond -->
        <path d="M 455 170 L 515 170" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- DECISION DIAMOND: Confidence >= 50%? -->
        <g id="grp-decision" class="flow-node" onclick="setIngestionInfo('CONFIDENCE DECISION', 'Threshold >= 50.0%', 'Table only ingested if real timestamps are confirmed across row values.')">
          <polygon points="585,115 655,170 585,225 515,170" fill="#1e1b4b" stroke="#818cf8" stroke-width="2"/>
          <text x="585" y="165" fill="#c7d2fe" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">CONFIDENCE</text>
          <text x="585" y="180" fill="#fff" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">&ge; 50% ?</text>
        </g>

        <!-- REJECT BRANCH (DOWNWARDS) -->
        <path d="M 585 225 L 585 330 L 460 330" class="flow-line" stroke="#f43f5e" stroke-width="2" marker-end="url(#arrow-rose)"/>
        <text x="600" y="270" fill="#f43f5e" font-size="11" font-family="monospace" font-weight="bold">&lt; 50% NO</text>

        <g id="grp-audit" class="flow-node" onclick="setIngestionInfo('AUDIT MANIFEST', 'recon_manifest.json (No Silent Drop)', 'Non-compliant tables preserved in manifest for safety certification audit.')">
          <rect x="290" y="300" width="165" height="60" rx="8" fill="#450a0a" stroke="#f43f5e" stroke-width="1.5"/>
          <text x="372" y="325" fill="#fda4af" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">AUDIT MANIFEST</text>
          <text x="372" y="345" fill="#fff" font-size="11" font-family="monospace" text-anchor="middle">Flagged &amp; Logged</text>
        </g>

        <!-- ACCEPT BRANCH (RIGHT) -->
        <path d="M 655 170 L 715 170" class="flow-line-active" marker-end="url(#arrow-emerald)"/>
        <text x="665" y="160" fill="#10b981" font-size="11" font-family="monospace" font-weight="bold">&ge; 50% YES</text>

        <!-- STEP 2: node_mapping.py -->
        <g id="grp-mapping" class="flow-node" onclick="setIngestionInfo('STEP 2: node_mapping.py', 'Declarative Hardware Rack Decoupling', 'Routes NODE_A -> Left Rack, NODE_B -> Right Rack, NODE_C -> Auxiliary Rack.')">
          <rect x="720" y="120" width="180" height="100" rx="10" fill="#0f172a" stroke="#3b82f6" stroke-width="2"/>
          <rect x="730" y="130" width="80" height="18" rx="4" fill="#1d4ed8"/>
          <text x="770" y="143" fill="#fff" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">STEP 2</text>
          <text x="810" y="165" fill="#60a5fa" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">node_mapping.py</text>
          <text x="810" y="185" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">Hardware Rack Map</text>
          <text x="810" y="202" fill="#60a5fa" font-size="10" font-family="monospace" text-anchor="middle">Left / Right / Aux</text>
        </g>

        <!-- Connector to STEP 3 -->
        <path d="M 900 170 L 955 170" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- STEP 3: extractor.py -->
        <g id="grp-eav" class="flow-node" onclick="setIngestionInfo('STEP 3: extractor.py', 'Schema-Agnostic Entity-Attribute-Value', 'Builds IngestionRecord: Universal coordinates + dynamic fields dict[str, Any].')">
          <rect x="960" y="120" width="180" height="100" rx="10" fill="#0f172a" stroke="#10b981" stroke-width="2"/>
          <rect x="970" y="130" width="80" height="18" rx="4" fill="#047857"/>
          <text x="1010" y="143" fill="#fff" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">STEP 3</text>
          <text x="1050" y="165" fill="#34d399" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">extractor.py</text>
          <text x="1050" y="185" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">EAV Normalizer</text>
          <text x="1050" y="202" fill="#34d399" font-size="10" font-family="monospace" text-anchor="middle">fields: dict[str, Any]</text>
        </g>

        <!-- Connector to STEP 4 -->
        <path d="M 1140 170 L 1195 170" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- STEP 4: timestamps.py -->
        <g id="grp-clock" class="flow-node" onclick="setIngestionInfo('STEP 4: timestamps.py', 'Monotonic Clock Normalization', 'Formula: tau = 3600*H + 60*M + S + delta_s. Detects jitter & midnight rollover.')">
          <rect x="1200" y="120" width="170" height="100" rx="10" fill="#0f172a" stroke="#f59e0b" stroke-width="2"/>
          <rect x="1210" y="130" width="80" height="18" rx="4" fill="#b45309"/>
          <text x="1250" y="143" fill="#fff" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">STEP 4</text>
          <text x="1285" y="165" fill="#fbbf24" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">timestamps.py</text>
          <text x="1285" y="185" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">Monotonic &tau; Float</text>
          <text x="1285" y="202" fill="#fbbf24" font-size="10" font-family="monospace" text-anchor="middle">&tau; = 3600&middot;H + 60&middot;M + S</text>
        </g>

        <!-- Connector to FINAL STORE -->
        <path d="M 1285 220 L 1285 300 L 1050 300" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- FINAL BUFFER STORE -->
        <g id="grp-store" class="flow-node" onclick="setIngestionInfo('NORMALIZED INGESTION BUFFER', 'DuckDB & Parquet Storage', 'Zero data loss, 100% preservation of milliseconds, audit-ready coordinates.')">
          <rect x="850" y="270" width="195" height="60" rx="8" fill="#1e1b4b" stroke="#c084fc" stroke-width="2"/>
          <text x="947" y="295" fill="#e9d5ff" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">INGESTION STORE</text>
          <text x="947" y="315" fill="#fff" font-size="12" font-family="monospace" text-anchor="middle">DuckDB &bull; Parquet Record</text>
        </g>
      </svg>

      <!-- Inspector Tray -->
      <div class="inspector-tray">
        <div class="inspector-meta">
          <div class="meta-chip">
            <span class="label">COMPONENT:</span>
            <span class="val" id="ing-info-title">STEP 1: recon.py</span>
          </div>
          <div class="meta-chip">
            <span class="label">MECHANIC:</span>
            <span class="val" id="ing-info-sub">Cell Value Regex Profiler (_SAMPLE_SIZE=50)</span>
          </div>
          <div class="meta-chip">
            <span class="label">VERDICT:</span>
            <span class="val" id="ing-info-desc">Calculates Confidence Score = Valid_TS / Non_Empty. Ignores misleading header names.</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================================================== -->
  <!-- TAB 2: DATA TRANSLATION ARCHITECTURE (DIAGRAM) -->
  <!-- ==================================================== -->
  <section id="pane-translation" class="tab-pane">
    <div class="canvas-card">
      <div class="canvas-header">
        <div class="canvas-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
          THE 3-LAYER TRANSLATION ARCHITECTURE & DECODER PIPELINE
        </div>
        <div class="canvas-tools">
          <div class="tool-pill active" onclick="setTranslatorPreset('all')">COMPLETE ENGINE</div>
          <div class="tool-pill" onclick="setTranslatorPreset('fault')">BITE 6025</div>
          <div class="tool-pill" onclick="setTranslatorPreset('trap')">TRAP 402656480</div>
          <div class="tool-pill" onclick="setTranslatorPreset('arinc')">ARINC 4294967172</div>
          <div class="tool-pill" onclick="setTranslatorPreset('pilot')">PILOT 4869</div>
        </div>
      </div>

      <!-- 3-Layer Translation Architecture SVG -->
      <svg id="svg-translation-flow" class="diagram" viewBox="0 0 1400 520">
        <!-- INPUT COLUMN: Cryptic Machine Telemetry -->
        <g id="grp-raw-stream" class="flow-node">
          <rect x="40" y="40" width="220" height="420" rx="10" fill="#0f172a" stroke="#f43f5e" stroke-width="1.5"/>
          <text x="150" y="70" fill="#fda4af" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">RAW CRYPTIC SIGNALS</text>
          <text x="150" y="88" fill="#64748b" font-size="10" font-family="monospace" text-anchor="middle">Machine Register Dumps</text>

          <!-- Input signal 1: BITE -->
          <g id="raw-node-bite" onclick="setTranslatorPreset('fault')">
            <rect x="55" y="110" width="190" height="55" rx="6" fill="#1e1b4b" stroke="#818cf8"/>
            <text x="150" y="132" fill="#c7d2fe" font-size="10" font-family="monospace" text-anchor="middle">BITE CODE</text>
            <text x="150" y="152" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">6074 / 6025</text>
          </g>

          <!-- Input signal 2: Stack Trap -->
          <g id="raw-node-trap" onclick="setTranslatorPreset('trap')">
            <rect x="55" y="180" width="190" height="55" rx="6" fill="#1e1b4b" stroke="#818cf8"/>
            <text x="150" y="202" fill="#c7d2fe" font-size="10" font-family="monospace" text-anchor="middle">MEMORY ADDRESS</text>
            <text x="150" y="222" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">402656480</text>
          </g>

          <!-- Input signal 3: Command Word -->
          <g id="raw-node-arinc" onclick="setTranslatorPreset('arinc')">
            <rect x="55" y="250" width="190" height="55" rx="6" fill="#1e1b4b" stroke="#818cf8"/>
            <text x="150" y="272" fill="#c7d2fe" font-size="10" font-family="monospace" text-anchor="middle">COMMAND WORD</text>
            <text x="150" y="292" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">4294967172</text>
          </g>

          <!-- Input signal 4: Key Matrix -->
          <g id="raw-node-pilot" onclick="setTranslatorPreset('pilot')">
            <rect x="55" y="320" width="190" height="55" rx="6" fill="#1e1b4b" stroke="#818cf8"/>
            <text x="150" y="342" fill="#c7d2fe" font-size="10" font-family="monospace" text-anchor="middle">BUTTON PUSH</text>
            <text x="150" y="362" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">4869</text>
          </g>

          <!-- Input signal 5: Redundancy Status -->
          <g id="raw-node-redundancy">
            <rect x="55" y="390" width="190" height="55" rx="6" fill="#1e1b4b" stroke="#818cf8"/>
            <text x="150" y="412" fill="#c7d2fe" font-size="10" font-family="monospace" text-anchor="middle">CROSS-TALK STATUS</text>
            <text x="150" y="432" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">Dual: 1 | Opp: 0</text>
          </g>
        </g>

        <!-- Vectors to LAYER 1 -->
        <path d="M 260 137 L 340 137" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 260 207 L 340 207" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 260 277 L 340 277" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 260 347 L 340 347" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 260 417 L 340 417" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- LAYER 1: DOMAIN DICTIONARIES -->
        <g id="grp-layer1">
          <rect x="345" y="40" width="280" height="420" rx="10" fill="#0b1329" stroke="#38bdf8" stroke-width="2"/>
          <text x="485" y="70" fill="#38bdf8" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">LAYER 1: DOMAIN MATRICES</text>
          <text x="485" y="88" fill="#64748b" font-size="10" font-family="monospace" text-anchor="middle">Hardware &amp; Aerospace Specs</text>

          <!-- L1 Decode 1 -->
          <rect x="360" y="110" width="250" height="55" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="485" y="132" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">BITE_FAULT_MAP[6025]</text>
          <text x="485" y="152" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">PID 653 Lookup Fail</text>

          <!-- L1 Decode 2 -->
          <rect x="360" y="180" width="250" height="55" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="485" y="202" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">HEX CONVERTER</text>
          <text x="485" y="222" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">0x18000CE0 (Stack Trap)</text>

          <!-- L1 Decode 3 -->
          <rect x="360" y="250" width="250" height="55" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="485" y="272" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">COMMAND_WORD_MAP</text>
          <text x="485" y="292" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">0xFFFFFE84 Invalidate</text>

          <!-- L1 Decode 4 -->
          <rect x="360" y="320" width="250" height="55" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="485" y="342" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">MCDU_BUTTON_MAP[4869]</text>
          <text x="485" y="362" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">INIT (Initialization) Key</text>

          <!-- L1 Decode 5 -->
          <rect x="360" y="390" width="250" height="55" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="485" y="412" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">REDUNDANCY_MODE_MAP</text>
          <text x="485" y="432" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">Single FMS (Degraded)</text>
        </g>

        <!-- Vectors to LAYER 2 -->
        <path d="M 625 250 L 705 250" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- LAYER 2: SUBSYSTEM SYNTHESIS ROUTER -->
        <g id="grp-layer2">
          <rect x="710" y="40" width="300" height="420" rx="10" fill="#0f172a" stroke="#10b981" stroke-width="2"/>
          <text x="860" y="70" fill="#10b981" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">LAYER 2: CONTEXT SYNTHESIS</text>
          <text x="860" y="88" fill="#64748b" font-size="10" font-family="monospace" text-anchor="middle">synthesize_event_headline()</text>

          <!-- Branch 1: Fault Family -->
          <rect x="725" y="120" width="270" height="85" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="860" y="142" fill="#f43f5e" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">family == "Fault"</text>
          <text x="860" y="162" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">Failure + RTOS Daemon + Auto Action</text>
          <text x="860" y="182" fill="#34d399" font-size="9" font-family="monospace" text-anchor="middle">Deos Service Restart Triggered</text>

          <!-- Branch 2: State Family -->
          <rect x="725" y="225" width="270" height="85" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="860" y="247" fill="#f59e0b" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">family == "STATE"</text>
          <text x="860" y="267" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">Cross-Talk Timeout Detection</text>
          <text x="860" y="287" fill="#34d399" font-size="9" font-family="monospace" text-anchor="middle">Partner Isolated Fail-Passive</text>

          <!-- Branch 3: Pilot Family -->
          <rect x="725" y="330" width="270" height="85" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="860" y="352" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">family == "CI_BPQ"</text>
          <text x="860" y="372" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">Crew Station + Nav Purpose</text>
          <text x="860" y="392" fill="#34d399" font-size="9" font-family="monospace" text-anchor="middle">Captain / FO Flight Level Input</text>
        </g>

        <!-- Vectors to OUTPUT -->
        <path d="M 1010 250 L 1080 250" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- LAYER 3: EVALUATOR OUTPUT CARD -->
        <g id="grp-output">
          <rect x="1085" y="40" width="280" height="420" rx="10" fill="#1e1b4b" stroke="#a855f7" stroke-width="2"/>
          <text x="1225" y="70" fill="#c084fc" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">OUTPUT INTELLIGENCE</text>
          <text x="1225" y="88" fill="#a5b4fc" font-size="10" font-family="monospace" text-anchor="middle">Evaluator Clear Event</text>

          <rect x="1100" y="115" width="250" height="150" rx="6" fill="#0f172a" stroke="#6366f1"/>
          <text x="1225" y="140" fill="#a5b4fc" font-size="10" font-family="monospace" text-anchor="middle">SYNTHESIZED HEADLINE</text>
          <text x="1225" y="165" fill="#fff" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle" id="out-headline-1">BITE Fault 6025</text>
          <text x="1225" y="185" fill="#38bdf8" font-size="10" font-family="monospace" text-anchor="middle" id="out-headline-2">Process ID Lookup Fail</text>
          <text x="1225" y="215" fill="#94a3b8" font-size="9" font-family="monospace" text-anchor="middle">Auto Recovery: FMS Restart</text>
          <text x="1225" y="240" fill="#f43f5e" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">[CRITICAL DIAGNOSTIC]</text>

          <rect x="1100" y="280" width="250" height="150" rx="6" fill="#0f172a" stroke="#6366f1"/>
          <text x="1225" y="305" fill="#a5b4fc" font-size="10" font-family="monospace" text-anchor="middle">REDUNDANCY VERDICT</text>
          <text x="1225" y="330" fill="#fbbf24" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">Partner FMS Isolated</text>
          <text x="1225" y="355" fill="#94a3b8" font-size="9" font-family="monospace" text-anchor="middle">Cross-Talk Timeout on Node A</text>
          <text x="1225" y="380" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">Single FMS Mode Active</text>
          <text x="1225" y="405" fill="#f59e0b" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">[REDUNDANCY LOSS]</text>
        </g>
      </svg>
    </div>
  </section>

  <!-- ==================================================== -->
  <!-- TAB 3: DATA CORRELATION & CAUSAL DAG (NETWORK) -->
  <!-- ==================================================== -->
  <section id="pane-correlation" class="tab-pane">
    <div class="canvas-card">
      <div class="canvas-header">
        <div class="canvas-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
          CAUSAL DIRECTED ACYCLIC GRAPH (DAG) &amp; BLAST RADIUS PROPAGATION
        </div>
        <div class="canvas-tools">
          <div class="tool-pill active" onclick="highlightDagPath('all')">COMPLETE NETWORK</div>
          <div class="tool-pill" onclick="highlightDagPath('root')">ROOT CAUSE (6074)</div>
          <div class="tool-pill" onclick="highlightDagPath('mutex')">MUTEX (6029)</div>
          <div class="tool-pill" onclick="highlightDagPath('deadline')">DEADLINE (6000)</div>
          <div class="tool-pill" onclick="highlightDagPath('receivers')">RECEIVERS (11631-3)</div>
        </div>
      </div>

      <!-- Causal DAG SVG Diagram -->
      <svg id="svg-dag-network" class="diagram" viewBox="0 0 1400 500">
        <!-- Blast Radius Concentric Background Rings -->
        <g id="grp-blast-rings" transform="translate(160, 250)">
          <circle r="90" fill="none" stroke="rgba(244, 63, 94, 0.15)" stroke-width="1.5" stroke-dasharray="4 4"/>
          <circle r="220" fill="none" stroke="rgba(244, 63, 94, 0.1)" stroke-width="1.5" stroke-dasharray="4 4"/>
          <circle r="360" fill="none" stroke="rgba(244, 63, 94, 0.06)" stroke-width="1.5" stroke-dasharray="4 4"/>
        </g>

        <!-- ROOT NODE: 6074 -->
        <g id="dag-node-6074" class="flow-node" onclick="setDagInfo('ROOT CAUSE: BITE 6074', 'Navigation Repository File EOF Failure', 'Premature EOF while reading flight navigation artifacts from disk. Triggered 5 downstream RTOS failures.')">
          <circle cx="160" cy="250" r="48" fill="#4c0519" stroke="#f43f5e" stroke-width="3"/>
          <circle cx="160" cy="250" r="54" fill="none" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="6 4" class="flow-line-active"/>
          <text x="160" y="240" fill="#fecdd3" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">ROOT CAUSE</text>
          <text x="160" y="258" fill="#fff" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">6074</text>
          <text x="160" y="274" fill="#fda4af" font-size="9" font-family="monospace" text-anchor="middle">Nav File EOF</text>
        </g>

        <!-- Edges from 6074 to Tier 1 -->
        <path d="M 215 230 L 400 130" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 220 250 L 400 250" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 215 270 L 400 370" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- TIER 1 NODES: 6025, 6052, 6035 -->
        <g id="dag-node-6025" class="flow-node" onclick="setDagInfo('TIER 1: BITE 6025', 'Process ID Lookup Failure (PID 653)', 'Deos daemon could not resolve process PID due to uninitialized public FMS navigation partition.')">
          <rect x="410" y="95" width="180" height="70" rx="8" fill="#0f172a" stroke="#38bdf8" stroke-width="2"/>
          <text x="500" y="122" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">TIER 1 / PID LOOKUP</text>
          <text x="500" y="142" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">BITE Fault 6025</text>
          <text x="500" y="156" fill="#38bdf8" font-size="9" font-family="monospace" text-anchor="middle">Daemon PID 653</text>
        </g>

        <g id="dag-node-6052" class="flow-node" onclick="setDagInfo('TIER 1: BITE 6052', 'Dynamic Library Load Failure', 'RTOS loader could not map shared navigation library libpssl.so.')">
          <rect x="410" y="215" width="180" height="70" rx="8" fill="#0f172a" stroke="#38bdf8" stroke-width="2"/>
          <text x="500" y="242" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">TIER 1 / LIB MAP</text>
          <text x="500" y="262" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">BITE Fault 6052</text>
          <text x="500" y="276" fill="#38bdf8" font-size="9" font-family="monospace" text-anchor="middle">libpssl.so Map</text>
        </g>

        <g id="dag-node-6035" class="flow-node" onclick="setDagInfo('TIER 1: BITE 6035', 'Inter-Process Service Bind Failure', 'Callback handler registration failed in Deos process table.')">
          <rect x="410" y="335" width="180" height="70" rx="8" fill="#0f172a" stroke="#38bdf8" stroke-width="2"/>
          <text x="500" y="362" fill="#94a3b8" font-size="10" font-family="monospace" text-anchor="middle">TIER 1 / IPC BIND</text>
          <text x="500" y="382" fill="#fff" font-size="13" font-family="monospace" font-weight="bold" text-anchor="middle">BITE Fault 6035</text>
          <text x="500" y="396" fill="#38bdf8" font-size="9" font-family="monospace" text-anchor="middle">Missing Callback</text>
        </g>

        <!-- Edges to TIER 2: Mutex 6029 -->
        <path d="M 590 370 L 710 320" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 590 250 L 710 300" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- TIER 2: Mutex Lock 6029 -->
        <g id="dag-node-6029" class="flow-node" onclick="setDagInfo('TIER 2: BITE 6029', 'OS Semaphore Mutex Lock Timeout', 'IPC bind timeout caused kernel mutual exclusion lock to block indefinitely.')">
          <rect x="720" y="270" width="190" height="80" rx="8" fill="#1e1b4b" stroke="#f59e0b" stroke-width="2"/>
          <text x="815" y="298" fill="#fde68a" font-size="10" font-family="monospace" text-anchor="middle">TIER 2 / MUTEX LOCK</text>
          <text x="815" y="320" fill="#fff" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">BITE Fault 6029</text>
          <text x="815" y="338" fill="#f59e0b" font-size="9" font-family="monospace" text-anchor="middle">Semaphore Timeout</text>
        </g>

        <!-- Edge to TIER 3: Deadline Miss 6000 -->
        <path d="M 910 310 L 1000 310" class="flow-line-active" marker-end="url(#arrow-rose)"/>

        <!-- TIER 3: Deadline Miss 6000 -->
        <g id="dag-node-6000" class="flow-node" onclick="setDagInfo('TIER 3: BITE 6000', 'RTOS Real-Time Deadline Missed', 'Blocked mutex thread exceeded RTOS CPU scheduling slice, killing Nav Core Daemon Task 35.')">
          <rect x="1010" y="270" width="180" height="80" rx="8" fill="#450a0a" stroke="#f43f5e" stroke-width="2"/>
          <text x="1100" y="298" fill="#fda4af" font-size="10" font-family="monospace" text-anchor="middle">TIER 3 / CPU DEADLINE</text>
          <text x="1100" y="320" fill="#fff" font-size="14" font-family="monospace" font-weight="bold" text-anchor="middle">BITE Fault 6000</text>
          <text x="1100" y="338" fill="#f43f5e" font-size="9" font-family="monospace" text-anchor="middle">Scheduling Slice Expired</text>
        </g>

        <!-- Edges to TIER 4: Receivers 11631-3 -->
        <path d="M 1190 290 L 1260 210" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 1190 310 L 1260 310" class="flow-line-active" marker-end="url(#arrow-cyan)"/>
        <path d="M 1190 330 L 1260 410" class="flow-line-active" marker-end="url(#arrow-cyan)"/>

        <!-- TIER 4: Receivers 11631-3 -->
        <g id="dag-node-11631" class="flow-node">
          <rect x="1270" y="180" width="110" height="50" rx="6" fill="#080d18" stroke="#64748b"/>
          <text x="1325" y="202" fill="#94a3b8" font-size="9" font-family="monospace" text-anchor="middle">RX 1 DROP</text>
          <text x="1325" y="220" fill="#fff" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">11631 VOR</text>
        </g>
        <g id="dag-node-11632" class="flow-node">
          <rect x="1270" y="285" width="110" height="50" rx="6" fill="#080d18" stroke="#64748b"/>
          <text x="1325" y="307" fill="#94a3b8" font-size="9" font-family="monospace" text-anchor="middle">RX 2 DROP</text>
          <text x="1325" y="325" fill="#fff" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">11632 DME</text>
        </g>
        <g id="dag-node-11633" class="flow-node">
          <rect x="1270" y="385" width="110" height="50" rx="6" fill="#080d18" stroke="#64748b"/>
          <text x="1325" y="407" fill="#94a3b8" font-size="9" font-family="monospace" text-anchor="middle">MMR DROP</text>
          <text x="1325" y="425" fill="#fff" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">11633 ILS</text>
        </g>
      </svg>

      <!-- DAG Inspector Tray -->
      <div class="inspector-tray">
        <div class="inspector-meta">
          <div class="meta-chip">
            <span class="label">NODE:</span>
            <span class="val" id="dag-info-node">ROOT CAUSE: BITE 6074</span>
          </div>
          <div class="meta-chip">
            <span class="label">CLASSIFICATION:</span>
            <span class="val" id="dag-info-class">Navigation Repository File EOF Failure</span>
          </div>
          <div class="meta-chip">
            <span class="label">BLAST RADIUS:</span>
            <span class="val" id="dag-info-blast" style="color:var(--rose);">5 DOWNSTREAM SUBSYSTEMS AFFECTED</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================================================== -->
  <!-- TAB 4: FLIGHT STORY MISSION PROFILE (TRAJECTORY) -->
  <!-- ==================================================== -->
  <section id="pane-flightstory" class="tab-pane">
    <div class="canvas-card">
      <div class="canvas-header">
        <div class="canvas-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
          FLIGHT STORY 2D TRAJECTORY &amp; INCIDENT CALLOUT PROFILE
        </div>
        <div class="canvas-tools">
          <div class="tool-pill active" onclick="setFlightStage('all')">COMPLETE MISSION</div>
          <div class="tool-pill" onclick="setFlightStage('gate')">1. GATE PARKED</div>
          <div class="tool-pill" onclick="setFlightStage('climb')">2. CLIMB ASCENT</div>
          <div class="tool-pill" onclick="setFlightStage('cruise')">3. CRUISE LEVEL</div>
          <div class="tool-pill" onclick="setFlightStage('descent')">4. DESCENT &amp; LAND</div>
        </div>
      </div>

      <!-- 2D Mission Trajectory Profile SVG -->
      <svg id="svg-flight-profile" class="diagram" viewBox="0 0 1400 480">
        <defs>
          <linearGradient id="grad-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(56, 189, 248, 0.25)"/>
            <stop offset="100%" stop-color="rgba(56, 189, 248, 0.0)"/>
          </linearGradient>
        </defs>

        <!-- Y-Axis Altitude Grid Lines -->
        <line x1="80" y1="80" x2="1350" y2="80" stroke="#1c2842" stroke-width="1" stroke-dasharray="4 4"/>
        <text x="60" y="85" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">18,000 ft</text>

        <line x1="80" y1="160" x2="1350" y2="160" stroke="#1c2842" stroke-width="1" stroke-dasharray="4 4"/>
        <text x="60" y="165" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">12,000 ft</text>

        <line x1="80" y1="240" x2="1350" y2="240" stroke="#1c2842" stroke-width="1" stroke-dasharray="4 4"/>
        <text x="60" y="245" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">6,000 ft</text>

        <line x1="80" y1="320" x2="1350" y2="320" stroke="#1c2842" stroke-width="1" stroke-dasharray="4 4"/>
        <text x="60" y="325" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">1,000 ft</text>

        <line x1="80" y1="380" x2="1350" y2="380" stroke="#334155" stroke-width="1.5"/>
        <text x="60" y="385" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">0 ft (GND)</text>

        <!-- Shaded Sky Polygon under path -->
        <polygon points="80,380 240,380 440,80 880,80 1100,280 1250,380 1350,380 1350,380 80,380" fill="url(#grad-sky)"/>

        <!-- The Flight Path Curve -->
        <path id="flight-curve" d="M 80 380 L 240 380 Q 320 380 440 80 L 880 80 Q 980 80 1100 280 L 1250 380 L 1350 380" fill="none" stroke="#38bdf8" stroke-width="3.5"/>

        <!-- Interactive Incident Callout Pins -->
        <!-- PIN 1: Gate Incident -->
        <g id="pin-1" class="flow-node" onclick="setFlightPin(1)">
          <line x1="160" y1="380" x2="160" y2="280" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="2 2"/>
          <circle cx="160" cy="380" r="5" fill="#f43f5e"/>
          <rect x="90" y="240" width="140" height="40" rx="6" fill="#450a0a" stroke="#f43f5e" stroke-width="1.5"/>
          <text x="160" y="258" fill="#fda4af" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">INCIDENT 1 &bull; GATE</text>
          <text x="160" y="272" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">BITE 6025 PID FAIL</text>
        </g>

        <!-- PIN 2: Pilot Cruise Entry -->
        <g id="pin-2" class="flow-node" onclick="setFlightPin(2)">
          <line x1="360" y1="210" x2="360" y2="120" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="2 2"/>
          <circle cx="360" cy="210" r="5" fill="#38bdf8"/>
          <rect x="290" y="80" width="140" height="40" rx="6" fill="#0c4a6e" stroke="#38bdf8" stroke-width="1.5"/>
          <text x="360" y="98" fill="#7dd3fc" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">PILOT ACTION</text>
          <text x="360" y="112" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">MCDU CRZ 15,000 FT</text>
        </g>

        <!-- PIN 3: Cruise Instruction Trap -->
        <g id="pin-3" class="flow-node" onclick="setFlightPin(3)">
          <line x1="660" y1="80" x2="660" y2="30" stroke="#f43f5e" stroke-width="1.5" stroke-dasharray="2 2"/>
          <circle cx="660" cy="80" r="6" fill="#f43f5e"/>
          <rect x="580" y="5" width="160" height="40" rx="6" fill="#450a0a" stroke="#f43f5e" stroke-width="1.5"/>
          <text x="660" y="22" fill="#fda4af" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">INCIDENT 2 &bull; CRUISE</text>
          <text x="660" y="36" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">TRAP 0x18000CE0</text>
        </g>

        <!-- PIN 4: Cross-Talk Timeout -->
        <g id="pin-4" class="flow-node" onclick="setFlightPin(4)">
          <line x1="820" y1="80" x2="820" y2="30" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="2 2"/>
          <circle cx="820" cy="80" r="6" fill="#f59e0b"/>
          <rect x="740" y="5" width="160" height="40" rx="6" fill="#451a03" stroke="#f59e0b" stroke-width="1.5"/>
          <text x="820" y="22" fill="#fde68a" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">INCIDENT 3 &bull; CRUISE</text>
          <text x="820" y="36" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">XTALK TIMEOUT (SINGLE)</text>
        </g>

        <!-- PIN 5: Descent & ILS -->
        <g id="pin-5" class="flow-node" onclick="setFlightPin(5)">
          <line x1="1100" y1="280" x2="1100" y2="200" stroke="#10b981" stroke-width="1.5" stroke-dasharray="2 2"/>
          <circle cx="1100" cy="280" r="5" fill="#10b981"/>
          <rect x="1030" y="160" width="140" height="40" rx="6" fill="#064e3b" stroke="#10b981" stroke-width="1.5"/>
          <text x="1100" y="178" fill="#6ee7b7" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">APPROACH PHASE</text>
          <text x="1100" y="192" fill="#fff" font-size="10" font-family="monospace" text-anchor="middle">ILS MODE 17 ACTIVE</text>
        </g>

        <!-- Current Aircraft Position Marker (Animated) -->
        <g id="aircraft-marker" transform="translate(660, 80)">
          <circle r="12" fill="rgba(56, 189, 248, 0.3)"/>
          <circle r="6" fill="#38bdf8"/>
        </g>
      </svg>

      <!-- Scrubber Bar -->
      <div class="scrubber-bar">
        <span style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">FLIGHT SCRUBBER:</span>
        <input type="range" id="flight-scrubber" class="scrubber-slider" min="0" max="100" value="50" oninput="scrubFlight(this.value)">
        <span id="scrub-phase-tag" style="font-family:var(--font-mono); font-size:12px; color:var(--cyan); font-weight:bold;">EN-ROUTE CRUISE (18,000 FT)</span>
      </div>

      <!-- Flight Story Inspector -->
      <div class="inspector-tray">
        <div class="inspector-meta">
          <div class="meta-chip">
            <span class="label">STAGE:</span>
            <span class="val" id="fp-stage">EN-ROUTE CRUISE</span>
          </div>
          <div class="meta-chip">
            <span class="label">ALTITUDE:</span>
            <span class="val" id="fp-alt">18,000.0 ft</span>
          </div>
          <div class="meta-chip">
            <span class="label">SIGNIFICANT EVENT:</span>
            <span class="val" id="fp-event">CPU Instruction Trap (0x18000CE0) Stack Boundary Trap</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================================================== -->
  <!-- TAB 5: AVIONICS TMR & VISUALIZATION (HUD) -->
  <!-- ==================================================== -->
  <section id="pane-visualization" class="tab-pane">
    <div class="canvas-card">
      <div class="canvas-header">
        <div class="canvas-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
          AVIONICS TMR SYSTEM SCHEMATIC &amp; COCKPIT PFD TELEMETRY HUD
        </div>
        <div class="canvas-tools">
          <div class="tool-pill active" id="btn-sync-toggle" onclick="toggleCrossTalkFault()">FAULT SIMULATOR: NORMAL (DUAL SYNC)</div>
        </div>
      </div>

      <!-- TMR Hardware Rack Schematic SVG -->
      <svg id="svg-tmr-schematic" class="diagram" viewBox="0 0 1400 320">
        <!-- NODE A RACK (Left) -->
        <g id="rack-node-a" class="flow-node">
          <rect x="60" y="40" width="340" height="230" rx="12" fill="#0f172a" stroke="#38bdf8" stroke-width="2.5"/>
          <rect x="80" y="60" width="90" height="20" rx="4" fill="#0284c7"/>
          <text x="125" y="74" fill="#fff" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">LEFT RACK</text>
          <text x="230" y="105" fill="#fff" font-size="18" font-family="monospace" font-weight="bold" text-anchor="middle">NODE A (FMS 1)</text>
          <text x="230" y="125" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">ACTIVE MASTER AUTHORITY</text>

          <rect x="80" y="150" width="300" height="95" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="100" y="175" fill="#94a3b8" font-size="10" font-family="monospace">RTOS: Deos Microkernel</text>
          <text x="100" y="195" fill="#94a3b8" font-size="10" font-family="monospace">Partition: Guidance Master</text>
          <text x="100" y="215" fill="#94a3b8" font-size="10" font-family="monospace">ARINC Bus: <tspan fill="#10b981" font-weight="bold">TRANSMITTING (CH A)</tspan></text>
          <text x="100" y="235" fill="#94a3b8" font-size="10" font-family="monospace">Standby Invalidate: <tspan fill="#38bdf8">0x00000000 (IDLE)</tspan></text>
        </g>

        <!-- ARINC-429 INTER-CHANNEL CROSS-TALK BUS -->
        <g id="rack-cross-talk">
          <path id="bus-wire-ab" d="M 400 155 L 600 155" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6 4" class="flow-line-active"/>
          <path id="bus-wire-ba" d="M 600 185 L 400 185" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6 4" class="flow-line-active"/>

          <rect x="420" y="100" width="160" height="50" rx="8" fill="#1e1b4b" stroke="#818cf8"/>
          <text x="500" y="120" fill="#c7d2fe" font-size="9" font-family="monospace" text-anchor="middle">CROSS-TALK BUS</text>
          <text x="500" y="138" fill="#38bdf8" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle" id="bus-status-text">ARINC-429 SYNC</text>
        </g>

        <!-- NODE B RACK (Right) -->
        <g id="rack-node-b" class="flow-node">
          <rect id="rect-node-b" x="600" y="40" width="340" height="230" rx="12" fill="#0f172a" stroke="#3b82f6" stroke-width="2.5"/>
          <rect x="620" y="60" width="90" height="20" rx="4" fill="#1d4ed8"/>
          <text x="665" y="74" fill="#fff" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">RIGHT RACK</text>
          <text x="770" y="105" fill="#fff" font-size="18" font-family="monospace" font-weight="bold" text-anchor="middle">NODE B (FMS 2)</text>
          <text id="node-b-role" x="770" y="125" fill="#60a5fa" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">STANDBY SHADOW MONITOR</text>

          <rect x="620" y="150" width="300" height="95" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="640" y="175" fill="#94a3b8" font-size="10" font-family="monospace">RTOS: Deos Microkernel</text>
          <text x="640" y="195" fill="#94a3b8" font-size="10" font-family="monospace">Partition: Shadow Sync</text>
          <text id="node-b-bus-txt" x="640" y="215" fill="#94a3b8" font-size="10" font-family="monospace">Opposite FMS: <tspan fill="#10b981" font-weight="bold">OK (HEALTHY)</tspan></text>
          <text id="node-b-state-txt" x="640" y="235" fill="#94a3b8" font-size="10" font-family="monospace">Authority: <tspan fill="#60a5fa">PASSIVE STANDBY</tspan></text>
        </g>

        <!-- NODE C RACK (Center Auxiliary) -->
        <g id="rack-node-c" class="flow-node">
          <rect x="1000" y="40" width="340" height="230" rx="12" fill="#0f172a" stroke="#a855f7" stroke-width="2.5"/>
          <rect x="1020" y="60" width="100" height="20" rx="4" fill="#6b21a8"/>
          <text x="1070" y="74" fill="#fff" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">CENTER RACK</text>
          <text x="1170" y="105" fill="#fff" font-size="18" font-family="monospace" font-weight="bold" text-anchor="middle">NODE C (FMS 3)</text>
          <text x="1170" y="125" fill="#c084fc" font-size="11" font-family="monospace" font-weight="bold" text-anchor="middle">MAJORITY VOTER / SPARE</text>

          <rect x="1020" y="150" width="300" height="95" rx="6" fill="#080d18" stroke="#334155"/>
          <text x="1040" y="175" fill="#94a3b8" font-size="10" font-family="monospace">RTOS: Deos Independent</text>
          <text x="1040" y="195" fill="#94a3b8" font-size="10" font-family="monospace">Partition: Byzantine Voter</text>
          <text x="1040" y="215" fill="#94a3b8" font-size="10" font-family="monospace">Trajectory: <tspan fill="#10b981">INDEPENDENT OPT</tspan></text>
          <text x="1040" y="235" fill="#94a3b8" font-size="10" font-family="monospace">Power Rail: <tspan fill="#c084fc">ISOLATED AUX</tspan></text>
        </g>
      </svg>

      <!-- Glass Cockpit HUD Gauges -->
      <div class="pfd-grid" style="margin-top:20px;">
        <!-- PFD Horizon -->
        <div class="gauge-panel">
          <div class="gauge-label">ATTITUDE DIRECTOR INDICATOR (ADI)</div>
          <div class="pfd-horizon">
            <div class="pfd-crosshair"></div>
          </div>
          <div style="margin-top:12px; font-family:var(--font-mono); font-size:11px; color:#38bdf8;">
            PITCH: +2.5&deg; &bull; ROLL: 0.0&deg;
          </div>
        </div>

        <!-- Altitude Tape -->
        <div class="gauge-panel">
          <div class="gauge-label">BAROMETRIC ALTITUDE</div>
          <div class="tape-box">
            <div class="tape-val" id="pfd-alt-tape">18,000</div>
            <div class="tape-unit">FEET MSL</div>
          </div>
          <div style="margin-top:14px; font-family:var(--font-mono); font-size:10px; color:#10b981;">
            VNAV: ON PROFILE
          </div>
        </div>

        <!-- Airspeed & Heading -->
        <div class="gauge-panel">
          <div class="gauge-label">VELOCITY &amp; HEADING</div>
          <div class="tape-box">
            <div class="tape-val" id="pfd-spd-tape">420.0</div>
            <div class="tape-unit">KNOTS TAS</div>
          </div>
          <div style="margin-top:14px; font-family:var(--font-mono); font-size:10px; color:#c084fc;">
            HDG: 284.0&deg; MAG TRACK
          </div>
        </div>
      </div>
    </div>
  </section>

</main>

<script>
// Tab switcher
function showTab(tabId) {{
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

  const targetPane = document.getElementById('pane-' + tabId);
  if (targetPane) targetPane.classList.add('active');

  const tabNames = ['ingestion', 'translation', 'correlation', 'flightstory', 'visualization'];
  const idx = tabNames.indexOf(tabId);
  if (idx !== -1) {{
    document.querySelectorAll('.tab-btn')[idx].classList.add('active');
  }}
}}

// Ingestion step highlights
function highlightIngestionStep(step) {{
  document.querySelectorAll('#pane-ingestion .tool-pill').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');

  if (step === 'recon') {{
    setIngestionInfo('STEP 1: recon.py', 'Structural Reconnaissance', 'Samples 50 cell values; regex tests confirm timestamp before database ingestion.');
  }} else if (step === 'mapping') {{
    setIngestionInfo('STEP 2: node_mapping.py', 'Subsystem Rack Decoupling', 'Physical files mapped to Left Rack (Node A), Right Rack (Node B), Aux Rack (Node C).');
  }} else if (step === 'eav') {{
    setIngestionInfo('STEP 3: extractor.py', 'EAV Schema-Agnostic Model', 'Stores universal coordinates + dynamic parameter fields: dict[str, Any].');
  }} else if (step === 'clock') {{
    setIngestionInfo('STEP 4: timestamps.py', 'Monotonic Clock Normalization', 'Formula tau = 3600*H + 60*M + S + delta_s. Detects jitter & midnight rollover.');
  }} else {{
    setIngestionInfo('END-TO-END PIPELINE', 'Multi-Subsystem Ingestion Engine', 'Complete 4-stage pipeline from heterogeneous HTML inputs to normalized storage.');
  }}
}}

function setIngestionInfo(title, sub, desc) {{
  document.getElementById('ing-info-title').innerText = title;
  document.getElementById('ing-info-sub').innerText = sub;
  document.getElementById('ing-info-desc').innerText = desc;
}}

// Translation presets
function setTranslatorPreset(preset) {{
  document.querySelectorAll('#pane-translation .tool-pill').forEach(p => p.classList.remove('active'));
  if (event && event.target && event.target.classList) {{
    event.target.classList.add('active');
  }}

  const h1 = document.getElementById('out-headline-1');
  const h2 = document.getElementById('out-headline-2');

  if (preset === 'fault') {{
    h1.innerText = "BITE Fault 6025";
    h2.innerText = "Process Identity Lookup Fail";
  }} else if (preset === 'trap') {{
    h1.innerText = "CPU Instruction Trap";
    h2.innerText = "0x18000CE0 (Stack Boundary)";
  }} else if (preset === 'arinc') {{
    h1.innerText = "ARINC-429 Command";
    h2.innerText = "0xFFFFFE84 (Standby Invalidate)";
  }} else if (preset === 'pilot') {{
    h1.innerText = "Captain MCDU Entry";
    h2.innerText = "Cruising Level 15,000 ft Assigned";
  }} else {{
    h1.innerText = "BITE Fault 6025";
    h2.innerText = "Deos RTOS Auto Restart";
  }}
}}

// DAG highlights
function highlightDagPath(path) {{
  document.querySelectorAll('#pane-correlation .tool-pill').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');

  if (path === 'root') {{
    setDagInfo('ROOT CAUSE: 6074', 'Navigation File Premature EOF', 'Root origin of all downstream Deos RTOS faults.');
  }} else if (path === 'mutex') {{
    setDagInfo('INTERMEDIATE: 6029', 'OS Semaphore Mutex Lock Timeout', 'IPC bind timeout causes microkernel mutex lock failure.');
  }} else if (path === 'deadline') {{
    setDagInfo('CONSEQUENCE: 6000', 'RTOS Real-Time Deadline Missed', 'Task 35 Nav Core Daemon misses scheduling slice.');
  }} else if (path === 'receivers') {{
    setDagInfo('HARDWARE FALLOUT', '11631 / 11632 / 11633 Receiver Drops', 'Navigation receivers drop off ARINC bus due to core daemon crash.');
  }} else {{
    setDagInfo('ROOT CAUSE: BITE 6074', 'Navigation Repository File EOF Failure', 'Blast Radius: 5 downstream subsystem nodes affected.');
  }}
}}

function setDagInfo(node, cls, blast) {{
  document.getElementById('dag-info-node').innerText = node;
  document.getElementById('dag-info-class').innerText = cls;
  document.getElementById('dag-info-blast').innerText = blast;
}}

// Flight scrubber
function scrubFlight(val) {{
  const marker = document.getElementById('aircraft-marker');
  const stage = document.getElementById('fp-stage');
  const alt = document.getElementById('fp-alt');
  const ev = document.getElementById('fp-event');
  const tag = document.getElementById('scrub-phase-tag');
  const altTape = document.getElementById('pfd-alt-tape');

  const x = 80 + (val / 100) * (1350 - 80);
  let y = 380;
  let curAlt = 0;
  let stageName = "PRE-FLIGHT GATE";
  let evText = "Nominal System Telemetry Heartbeat";

  if (val < 15) {{
    y = 380;
    curAlt = 0;
    stageName = "PRE-FLIGHT GATE";
    evText = "BITE Fault 6025 (PID 653 lookup failure) & FMS Service Restart";
  }} else if (val < 35) {{
    const pct = (val - 15) / 20;
    y = 380 - (pct * 300);
    curAlt = Math.round(pct * 18000);
    stageName = "CLIMB ASCENT";
    evText = "Captain MCDU Cruising Flight Level Entry (15,000 ft assigned)";
  }} else if (val < 65) {{
    y = 80;
    curAlt = 18000;
    stageName = "EN-ROUTE CRUISE";
    evText = "CPU Instruction Trap 0x18000CE0 & Cross-Talk Bus Timeout (Single Mode)";
  }} else if (val < 85) {{
    const pct = (val - 65) / 20;
    y = 80 + (pct * 300);
    curAlt = Math.round(18000 - (pct * 17000));
    stageName = "DESCENT & APPROACH";
    evText = "Vertical Guidance Profile Sequence Refresh & ILS Mode 17 Engaged";
  }} else {{
    y = 380;
    curAlt = 0;
    stageName = "TOUCHDOWN & ROLLOUT";
    evText = "Autoland rollout completed nominal on runway.";
  }}

  marker.setAttribute('transform', `translate(${{x}}, ${{y}})`);
  stage.innerText = stageName;
  alt.innerText = `${{curAlt.toLocaleString()}} ft`;
  ev.innerText = evText;
  tag.innerText = `${{stageName}} (${{curAlt.toLocaleString()}} FT)`;
  if (altTape) altTape.innerText = curAlt.toLocaleString();
}}

function setFlightPin(pin) {{
  if (pin === 1) scrubFlight(10);
  else if (pin === 2) scrubFlight(25);
  else if (pin === 3) scrubFlight(50);
  else if (pin === 4) scrubFlight(60);
  else if (pin === 5) scrubFlight(75);
}}

function setFlightStage(stage) {{
  document.querySelectorAll('#pane-flightstory .tool-pill').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');

  if (stage === 'gate') scrubFlight(5);
  else if (stage === 'climb') scrubFlight(25);
  else if (stage === 'cruise') scrubFlight(50);
  else if (stage === 'descent') scrubFlight(75);
  else scrubFlight(50);
}}

// Cross-talk fault simulation
let crossTalkDegraded = false;
function toggleCrossTalkFault() {{
  crossTalkDegraded = !crossTalkDegraded;
  const btn = document.getElementById('btn-sync-toggle');
  const busStatus = document.getElementById('bus-status-text');
  const wireAB = document.getElementById('bus-wire-ab');
  const wireBA = document.getElementById('bus-wire-ba');
  const rectB = document.getElementById('rect-node-b');
  const roleB = document.getElementById('node-b-role');
  const busTxtB = document.getElementById('node-b-bus-txt');
  const stateTxtB = document.getElementById('node-b-state-txt');

  if (crossTalkDegraded) {{
    btn.innerText = "FAULT INJECTED: CROSS-TALK TIMEOUT (ISOLATED)";
    btn.style.background = "var(--rose)";
    btn.style.color = "#fff";

    busStatus.innerText = "\u26a0 TIMEOUT (ISOLATE) \u26a0";
    busStatus.style.fill = "var(--rose)";
    wireAB.style.stroke = "var(--rose)";
    wireBA.style.stroke = "var(--rose)";

    rectB.style.stroke = "var(--rose)";
    roleB.innerText = "CHANNEL ISOLATED (FAIL-PASSIVE)";
    roleB.style.fill = "var(--rose)";
    busTxtB.innerHTML = 'Opposite FMS: <tspan fill="#f43f5e" font-weight="bold">0 (LOST HEARTBEAT)</tspan>';
    stateTxtB.innerHTML = 'Authority: <tspan fill="#f43f5e">STANDBY ISOLATED (0xFFFFFE84)</tspan>';
  }} else {{
    btn.innerText = "FAULT SIMULATOR: NORMAL (DUAL SYNC)";
    btn.style.background = "#080d18";
    btn.style.color = "var(--text-muted)";

    busStatus.innerText = "ARINC-429 SYNC";
    busStatus.style.fill = "var(--cyan)";
    wireAB.style.stroke = "var(--cyan)";
    wireBA.style.stroke = "var(--cyan)";

    rectB.style.stroke = "var(--blue)";
    roleB.innerText = "STANDBY SHADOW MONITOR";
    roleB.style.fill = "#60a5fa";
    busTxtB.innerHTML = 'Opposite FMS: <tspan fill="#10b981" font-weight="bold">OK (HEALTHY)</tspan>';
    stateTxtB.innerHTML = 'Authority: <tspan fill="#60a5fa">PASSIVE STANDBY</tspan>';
  }}
}}
</script>
</body>
</html>
"""

showcase_root = Path("showcase.html")
showcase_data = Path("data/showcase.html")

showcase_root.write_text(html_content, encoding="utf-8")
showcase_data.write_text(html_content, encoding="utf-8")
print(f"Generated visual-only showcase at: {showcase_root.resolve()} ({showcase_root.stat().st_size} bytes)")
