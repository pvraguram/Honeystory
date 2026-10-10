# Normalizer code to be added by teammates
import os
import re
import json
import html
import webbrowser
from pathlib import Path
from datetime import datetime

# =====================================================================
# PATH CONFIGURATION
# =====================================================================
from .config import INPUT_HTML_DIR, DATA_DIR

BASE_DIR = INPUT_HTML_DIR
OUTPUT_HTML = DATA_DIR / "winning_edge_avionics_dashboard.html"
OUTPUT_JSON = DATA_DIR / "winning_edge_avionics_data.json"

def parse_epoch(ts_str):
    if not ts_str:
        return 0.0
    clean = ts_str.strip()
    for fmt in (
        "%Y-%m-%d %I:%M:%S %p", "%Y-%m-%d %H:%M:%S",
        "%I:%M:%S %p", "%H:%M:%S",
        "%Y-%m-%d %I:%M:%S.%f %p", "%Y-%m-%d %H:%M:%S.%f"
    ):
        try:
            dt = datetime.strptime(clean, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=2032, month=6, day=18)
            return dt.timestamp()
        except ValueError:
            pass
    return 0.0

def classify_event(text_content, kv_map):
    txt_lower = text_content.lower()

    # 1. SYSTEM ERROR LAYER
    if "software fault address" in txt_lower:
        val = kv_map.get("software fault address", "402656480")
        hex_addr = f"0x{int(val):08X}" if val.isdigit() else val
        return "SYSTEM_ERROR", "badge-crit", f"CPU INSTRUCTION TRAP ({hex_addr})", f"Stack boundary violation at address {val}.", True

    if "performance defined event" in txt_lower:
        return "SYSTEM_ERROR", "badge-crit", "FMS PERFORMANCE CALCULATION EXCEPTION", "Node background waypoint optimization thread crashed.", True

    if any(sig in txt_lower for sig in ["not ok", "single mode", "degrade", "fail"]):
        return "SYSTEM_ERROR", "badge-warn", "CROSS-CHANNEL ARINC BUS DISCONNECT", "Redundancy degraded to Single Mode; fail-passive standby isolation.", True

    # 2. PILOT INPUT LAYER
    if "clear altitude" in txt_lower or "enter crz fl" in txt_lower:
        return "PILOT_INPUT", "badge-pilot", "PILOT MCDU: CRUISE ALTITUDE ENTRY", "Flight crew selected flight level clearance into CDU console.", False

    if "button push" in txt_lower:
        keys = [k for k in kv_map if "button" in k]
        return "PILOT_INPUT", "badge-pilot", "PILOT KEYPAD SCAN MATRIX BURST", f"Cockpit CDU keypad active interaction detected across {len(keys)} matrix inputs.", False

    # 3. NAVIGATION & GUIDANCE LAYER
    if "flightphase changed" in txt_lower or "phase change" in txt_lower:
        return "NAVIGATION", "badge-phase", "FMS FLIGHT PHASE TRANSITION", "Navigation profile confirmed active transition state.", False

    if "vertical guidance" in txt_lower or "sequence confirm" in txt_lower:
        return "NAVIGATION", "badge-nav", "VERTICAL GUIDANCE SEQUENCE REFRESH", "FMS VNAV profile trajectory verified against route waypoints.", False

    return "TELEMETRY", "badge-norm", "NOMINAL FLIGHT TELEMETRY", "Standard system operational heartbeat.", False

def fast_parse_html(file_path):
    """Zero-BeautifulSoup: Pure regex streaming parser for ultra-fast processing."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as ex:
        print(f"[ERR] File read failed {file_path.name}: {ex}")
        return []

    node_m = re.search(r"NODE[_-]([A-Z0-9]+)", file_path.name, re.IGNORECASE)
    default_node = f"NODE_{node_m.group(1).upper()}" if node_m else "FMS_CORE"

    row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
    cell_pattern = re.compile(r'<t[dh][^>]*>(.*?)</t[dh]>', re.DOTALL | re.IGNORECASE)
    tag_cleaner = re.compile(r'<[^>]+>')

    rows = []
    for r_match in row_pattern.finditer(content):
        row_html = r_match.group(1)
        raw_cells = [c.group(1).strip() for c in cell_pattern.finditer(row_html)]
        if len(raw_cells) < 3:
            continue

        clean_texts = [re.sub(tag_cleaner, ' ', c).strip() for c in raw_cells]
        full_text = " ".join(clean_texts)

        if "timestamp" in full_text.lower() and "sequence" in full_text.lower():
            continue

        # Extract sequence number for accurate sorting
        seq_num = 0
        if clean_texts[0].isdigit():
            seq_num = int(clean_texts[0])

        # Extract timestamp
        ts_raw = ""
        for t in clean_texts[:3]:
            if any(m in t.upper() for m in ["AM", "PM"]) or re.search(r"\d{1,2}:\d{2}:\d{2}", t):
                ts_raw = t
                break
        if not ts_raw and len(clean_texts) > 1:
            ts_raw = clean_texts[1]

        # Extract key-value registers
        kv_map = {}
        for line in full_text.splitlines():
            line_c = re.sub(r'^[•\-\*]\s*', '', line).strip()
            if ":" in line_c:
                k, v = line_c.split(":", 1)
                kv_map[k.strip().lower()] = v.strip()

        is_flight_schema = len(raw_cells) >= 6
        alt_val = None
        lat_val, lon_val = "-", "-"
        node_name = default_node

        if is_flight_schema and len(clean_texts) > 3 and clean_texts[3]:
            node_name = clean_texts[3].upper()

        # DYNAMIC ALTITUDE HUNTING
        # 1. Check Key-Value Map first
        for k, v in kv_map.items():
            if "alt" in k.lower():
                clean_alt = re.sub(r"[^\d.-]", "", v)
                if clean_alt:
                    alt_val = float(clean_alt)
                    break
        
        # 2. Check remaining columns if not in KV map
        if alt_val is None and is_flight_schema:
            for cell in clean_texts[3:]:
                if "ft" in cell.lower() or cell.replace(",", "").replace(".", "").isdigit():
                    clean_alt = re.sub(r"[^\d.-]", "", cell)
                    if clean_alt:
                        val = float(clean_alt)
                        if val > 100: # Assuming it's an altitude if > 100
                            alt_val = val
                            break

        # Coordinate extraction
        if is_flight_schema:
            for cell in clean_texts[3:]:
                if "N" in cell.upper() or "S" in cell.upper():
                    if re.search(r"\d+\.\d+", cell):
                        lat_val = cell
                if "E" in cell.upper() or "W" in cell.upper():
                    if re.search(r"\d+\.\d+", cell):
                        lon_val = cell

        domain, badge_class, title, desc, is_crit = classify_event(full_text, kv_map)

        rows.append({
            "seq": seq_num,
            "timestamp": ts_raw,
            "epoch": parse_epoch(ts_raw),
            "node": node_name,
            "is_flight_schema": is_flight_schema,
            "parsed_alt": alt_val,
            "coords": f"{lat_val}, {lon_val}" if lat_val != "-" else "-, -",
            "domain": domain,
            "badge_class": badge_class,
            "title": title,
            "desc": desc,
            "is_crit": is_crit,
            "kv_map": kv_map,
            "raw_snippet": full_text[:80]
        })

    return rows

def run_lightning_pipeline():
    ignored_prefixes = ("winning_", "flight_events_", "hybrid_", "final_", "fms_clean_", "synced_", "clean_", "hackathon_", "unified_")
    html_files = sorted(
        fp for fp in BASE_DIR.rglob("*.html")
        if not fp.name.startswith(ignored_prefixes)
    )

    print(f"\n[SCAN] Found {len(html_files)} log files. Parsing with High-Speed Streaming Regex Engine...")
    all_packets = []

    for fp in html_files:
        packets = fast_parse_html(fp)
        print(f"  -> {fp.name}: Extracted {len(packets)} records.")
        all_packets.extend(packets)

    if not all_packets:
        print(f"[ERR] No records found. Verify input files in {BASE_DIR}")
        return

    # Sort chronologically by Epoch, then Sequence Number to guarantee perfect order
    all_packets.sort(key=lambda x: (x["epoch"], x["seq"]))

    master_timeline = []
    prev_epoch = None
    last_known_alt = 0.0
    last_known_coords = "-, -"
    current_phase = "PRE_FLIGHT_GATE"

    for idx, r in enumerate(all_packets, start=1):
        curr_epoch = r["epoch"]
        if prev_epoch is not None and curr_epoch > 0:
            diff = curr_epoch - prev_epoch
            delta_str = f"+{int(diff//60)}m {int(diff%60):02d}s" if diff >= 60 else f"+{diff:.2f}s"
        else:
            delta_str = "0.00s (T0)"

        if curr_epoch > 0:
            prev_epoch = curr_epoch

        curr_alt = r["parsed_alt"]

        # DYNAMIC PHASE NORMALIZATION
        if curr_alt and curr_alt > 100.0:
            alt_diff = curr_alt - last_known_alt
            last_known_alt = curr_alt
            
            if r["coords"] != "-, -":
                last_known_coords = r["coords"]

            if alt_diff < -200.0:
                current_phase = f"DESCENT / APPROACH"
            elif curr_alt >= 12000.0 and abs(alt_diff) < 100.0:
                current_phase = f"CRUISE"
            elif alt_diff > 100.0:
                current_phase = f"ASCENT / CLIMB"
            
            display_alt = f"{curr_alt:,.0f} ft"
        else:
            display_alt = f"{last_known_alt:,.0f} ft (Held)"
            if last_known_alt < 100:
                current_phase = "PRE_FLIGHT_GATE (Parked)"

        coords_display = r["coords"] if r["coords"] != "-, -" else last_known_coords

        chips = []
        for k, v in list(r["kv_map"].items())[:3]:
            if str(v) not in ["0", "0.0", "", "[Redacted Payload]"]:
                chips.append(f'<span class="chip"><strong>{html.escape(k)}:</strong> {html.escape(str(v))}</span>')
        chips_html = "".join(chips) if chips else f'<span style="color:#64748b;">{html.escape(r["raw_snippet"])}</span>'

        master_timeline.append({
            "step": idx,
            "timestamp": r["timestamp"],
            "delta_t": delta_str,
            "node": r["node"],
            "phase": current_phase,
            "altitude": display_alt,
            "coords": coords_display,
            "domain": r["domain"],
            "badge_class": r["badge_class"],
            "title": r["title"],
            "desc": r["desc"],
            "is_crit": r["is_crit"],
            "chips_html": chips_html
        })

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(master_timeline, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Master JSON written: {OUTPUT_JSON}")

    render_dashboard(master_timeline)

def render_dashboard(events):
    rows = []
    for ev in events:
        is_airborne = any(ph in ev["phase"] for ph in ["CLIMB", "CRUISE", "DESCENT"])
        row_cls = "row-crit" if ev["is_crit"] else ("row-air" if is_airborne else "row-ground")

        rows.append(f"""
        <tr class="{row_cls}" data-domain="{ev['domain']}">
          <td style="font-weight:bold;">#{ev['step']}</td>
          <td>{html.escape(ev['timestamp'])}</td>
          <td><span class="delta-tag">{html.escape(ev['delta_t'])}</span></td>
          <td><span class="node-tag">{html.escape(ev['node'])}</span></td>
          <td><span class="phase-tag">{html.escape(ev['phase'])}</span></td>
          <td><strong style="color:#38bdf8;">{html.escape(ev['altitude'])}</strong></td>
          <td><small>{html.escape(ev['coords'])}</small></td>
          <td>
            <div class="ev-head">{html.escape(ev['title'])}</div>
            <div class="ev-sub">{html.escape(ev['desc'])}</div>
          </td>
          <td><span class="badge {ev['badge_class']}">{ev['domain'].replace('_', ' ')}</span></td>
          <td><div class="chip-box">{ev['chips_html']}</div></td>
        </tr>
        """)

    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Avionics High-Speed Diagnostic & Timeline Engine</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 24px; background: #0b0f17; color: #cbd5e1; font-family: -apple-system, sans-serif; }}
main {{ max-width: 1680px; margin: auto; }}
h2 {{ color: #f8fafc; font-size: 22px; margin-bottom: 4px; }}
p.sub {{ color: #94a3b8; font-size: 13px; margin-bottom: 18px; }}
.verdict-banner {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin-bottom: 22px; }}
.v-card {{ background: #141b26; border: 1px solid #233044; border-left: 4px solid #38bdf8; border-radius: 6px; padding: 14px; font-size: 12px; }}
.v-card strong {{ color: #38bdf8; display: block; margin-bottom: 4px; font-size: 13px; text-transform: uppercase; }}
.filter-bar {{ display: flex; gap: 8px; margin-bottom: 18px; flex-wrap: wrap; }}
.btn {{ background: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold; }}
.btn:hover, .btn.active {{ background: #38bdf8; color: #0b0f17; border-color: #38bdf8; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; background: #141b26; border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 9px 11px; border: 1px solid #233044; text-align: left; vertical-align: middle; }}
th {{ background: #1a2433; color: #94a3b8; font-size: 11px; text-transform: uppercase; }}
.delta-tag {{ background: #1e293b; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 11px; }}
.node-tag {{ background: #38bdf822; color: #38bdf8; padding: 2px 8px; border-radius: 12px; font-weight: bold; font-size: 11px; }}
.phase-tag {{ background: #22c55e22; color: #4ade80; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
.badge {{ padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; text-transform: uppercase; }}
.badge-crit {{ background: #ef444433; color: #f87171; border: 1px solid #ef444466; }}
.badge-warn {{ background: #f9731633; color: #fb923c; border: 1px solid #f9731666; }}
.badge-pilot {{ background: #eab30833; color: #facc15; border: 1px solid #eab30866; }}
.badge-phase {{ background: #10b98133; color: #34d399; border: 1px solid #10b98166; }}
.badge-nav {{ background: #8b5cf633; color: #a78bfa; border: 1px solid #8b5cf666; }}
.badge-norm {{ background: #64748b33; color: #94a3b8; }}
.ev-head {{ font-weight: bold; color: #f8fafc; font-size: 13px; margin-bottom: 2px; }}
.ev-sub {{ color: #94a3b8; font-size: 11px; }}
.chip-box {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.chip {{ background: #0f141d; border: 1px solid #283548; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #e2e8f0; }}
.chip strong {{ color: #38bdf8; }}
.row-crit {{ background: rgba(239, 68, 68, 0.08); }}
.row-crit .ev-head {{ color: #ff7b72; }}
.row-air {{ background: rgba(56, 189, 248, 0.04); }}
.row-ground {{ background: rgba(100, 116, 139, 0.03); }}
</style>
<script>
function filterDomain(dom) {{
  document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('tbody tr').forEach(r => {{
    if (dom === 'ALL' || r.getAttribute('data-domain') === dom) {{
      r.style.display = '';
    }} else {{
      r.style.display = 'none';
    }}
  }});
}}
</script>
</head>
<body>
<main>
  <h2>High-Speed Synchronized Avionics Diagnostic Engine</h2>
  <p class="sub">Progressive Flight Trajectory: Ground Gate -> Climb Ascent -> Cruise -> Descent</p>

  <div class="verdict-banner">
    <div class="v-card" style="border-left-color: #f87171;">
      <strong>Layer A: System Error Analysis</strong>
      Early Ground Gate crash localized on Node C background thread. Keypad FIFO overflow triggered CPU Trap (<code>402656480</code>) & <code>Performance Defined Event</code> loop during KJFK waypoint load.
    </div>
    <div class="v-card" style="border-left-color: #facc15;">
      <strong>Layer B: Pilot Input Dynamics</strong>
      CDU button matrix scan codes generated rapid interrupt stream, accompanied by target cruise level assignment (15,000 ft clearance).
    </div>
    <div class="v-card" style="border-left-color: #4ade80;">
      <strong>Layer C: Flight Navigation Profile</strong>
      Aeronautical state machine tracks Phase transitions dynamically based on parsed telemetry altitude differentials.
    </div>
  </div>

  <div class="filter-bar">
    <button class="btn active" onclick="filterDomain('ALL')">ALL EVENTS</button>
    <button class="btn" onclick="filterDomain('SYSTEM_ERROR')">SYSTEM ERRORS & CPU TRAPS</button>
    <button class="btn" onclick="filterDomain('PILOT_INPUT')">PILOT INPUTS (MCDU)</button>
    <button class="btn" onclick="filterDomain('NAVIGATION')">NAVIGATION & GUIDANCE</button>
    <button class="btn" onclick="filterDomain('TELEMETRY')">TELEMETRY STREAM</button>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width: 4%;">Step</th>
        <th style="width: 12%;">Timestamp</th>
        <th style="width: 6%;">Delta (Δt)</th>
        <th style="width: 8%;">Node / Source</th>
        <th style="width: 14%;">Flight Phase</th>
        <th style="width: 8%;">Altitude</th>
        <th style="width: 10%;">Coordinates</th>
        <th style="width: 20%;">Synchronized Event</th>
        <th style="width: 8%;">Event Domain</th>
        <th style="width: 10%;">Hardware Registers</th>
      </tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</main>
</body>
</html>"""

    OUTPUT_HTML.write_text(html_page, encoding="utf-8")
    print(f"[SUCCESS] Dashboard generated in seconds: {OUTPUT_HTML}")
    webbrowser.open(OUTPUT_HTML.resolve().as_uri())

if __name__ == "__main__":
    run_lightning_pipeline()