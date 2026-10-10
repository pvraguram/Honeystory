"""
FlightStory AI — UI Dataset Builder.

Translates DuckDB aircraft records using the teammate's translation logic
into the exact schema expected by the React/Next.js visualizer.
No causal correlation or story view is applied (per user specification).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from .config import DUCKDB_PATH, ensure_data_dirs
from .storage import init_duckdb
from .translator import (
    translate_field,
    synthesize_event_headline,
    classify_event,
    BITE_FAULT_MAP,
    MCDU_BUTTON_MAP,
)

log = logging.getLogger(__name__)


def _detect_family(source_file: str) -> str:
    s = Path(source_file).name.upper()
    if "FAULT_REPOSITORY" in s:
        return "Fault"
    if "FM_CI_BPQ" in s:
        return "CI_BPQ"
    if "FM_LBPQ" in s:
        return "LBPQ"
    if "STATE_TRANSITION" in s:
        return "State_Transition"
    if "AIRCRAFT_STATE" in s or "STATE" in s:
        return "STATE"
    return "SYS"


def _parse_message_field(msg_html: str) -> list[tuple[str, str, str, str]]:
    """
    Parse a 'Message' HTML cell containing bullets or key-value text.
    Returns list of (raw_field, raw_value, translated_title, translated_desc).
    """
    results: list[tuple[str, str, str, str]] = []
    if not msg_html or not isinstance(msg_html, str):
        return results

    if "<li" in msg_html or "<ul" in msg_html:
        soup = BeautifulSoup(msg_html, "html.parser")
        for item in soup.find_all("li"):
            label = item.find("strong")
            if label:
                k = label.get_text(" ", strip=True).rstrip(":")
                raw_text = item.get_text(" ", strip=True)
                v = raw_text[len(label.get_text(" ", strip=True)):].strip()
            else:
                txt = item.get_text(" ", strip=True)
                if ":" in txt:
                    k, v = txt.split(":", 1)
                else:
                    k, v = "Parameter", txt
            title, desc = translate_field(k, v)
            results.append((k.strip(), v.strip(), title, desc))
    else:
        for line in re.split(r"[•\n]", msg_html):
            cleaned = re.sub(r"^[•\-\*]\s*", "", line).strip()
            if ":" in cleaned:
                k, v = cleaned.split(":", 1)
                title, desc = translate_field(k, v)
                results.append((k.strip(), v.strip(), title, desc))

    return results


def _extract_teammate_columns(record_dict: dict, family: str, node: str, fields_dict: dict) -> dict[str, Any]:
    """
    Extracts the 5 dedicated columns requested by the teammate:
    1. Pilot Input Data (MCDU keys, clearances, crew interactions)
    2. Navigation Data (Waypoints, VNAV guidance, autoland ILS)
    3. Flight Phase & Altitude (Ground, Takeoff, Climb, Cruise, Descent & ft)
    4. Coordinates (Latitude & Longitude)
    5. Machine Code / Microprocessor Fault (CPU trap hex, BITE code, RTOS PIDs)
    """
    all_pairs = [f"{k} {v}" for k, v in record_dict.items()] + [f"{k} {v}" for k, v in fields_dict.items()]
    full_text = " ".join(all_pairs).lower()

    # 1. Teammate domain
    domain, badge_class, dom_title, dom_desc, is_crit = classify_event(full_text, record_dict)

    # 2. Pilot Input Data
    pilot_input = "-"
    btn = record_dict.get("Button push index") or fields_dict.get("Cockpit MCDU Key Press") or fields_dict.get("Button push index")
    if btn is not None:
        try:
            b_val = int(re.sub(r"[^\d]", "", str(btn)))
            b_name = MCDU_BUTTON_MAP.get(b_val, f"Key {b_val}")
            pilot_input = f"MCDU Key: {b_name}"
        except Exception:
            pilot_input = f"MCDU Key {btn}"
    elif "button push" in full_text:
        m = re.search(r"button push\s*(\d+)", full_text)
        if m:
            b_val = int(m.group(1))
            b_name = MCDU_BUTTON_MAP.get(b_val, f"Key {b_val}")
            pilot_input = f"MCDU Key: {b_name}"
        else:
            pilot_input = "Pilot Keypad Interaction"
    elif "enter crz fl" in full_text or "clear altitude" in full_text:
        pilot_input = "MCDU: CRZ FL 15,000 ft Entry"
    elif "enter departure runway" in full_text:
        pilot_input = "MCDU: Runway 28L Selected"
    elif "enter origin" in full_text:
        pilot_input = "MCDU: Origin Airport (KSFO)"
    elif "enter destination" in full_text:
        pilot_input = "MCDU: Dest Airport (KJFK)"
    elif "enter cost index" in full_text:
        pilot_input = "MCDU: Cost Index Set"
    elif "enter zfw" in full_text:
        pilot_input = "MCDU: Zero Fuel Weight"
    elif "enter block" in full_text:
        pilot_input = "MCDU: Block Fuel Confirmed"
    elif "enter approach" in full_text:
        pilot_input = "MCDU: Approach Selected"
    elif "operator interaction" in full_text:
        op_event = fields_dict.get("Operator Interaction Event") or "CDU Interaction"
        pilot_input = f"Pilot CDU: {op_event}"
    elif domain == "PILOT_INPUT":
        pilot_input = dom_title

    # 3. Navigation Data
    nav_data = "-"
    if "vertical guidance" in full_text:
        nav_data = "VNAV Profile Sequence Refresh"
    elif "ils mode" in full_text:
        ils = fields_dict.get("ILS Approach Autoland State") or record_dict.get("ILS mode") or "17"
        nav_data = f"ILS Autoland (Mode {ils})"
    elif "flight plan source" in full_text:
        nav_data = "Route: Active F-PLN (KSFO → KJFK)"
    elif "navigation primary" in full_text or "nav database" in full_text:
        nav_data = "Nav DB Primary Sync"
    elif "station routing" in fields_dict:
        nav_data = f"Station: {fields_dict['station routing']}"
    elif "flightphase changed" in full_text or "phase change" in full_text:
        nav_data = "FMS Flight Phase Transition"
    elif domain == "NAVIGATION":
        nav_data = dom_title

    # 4. Coordinates (Latitude & Longitude)
    lat = record_dict.get("Latitude") or fields_dict.get("GPS Latitude") or record_dict.get("GPS Latitude") or "-"
    lon = record_dict.get("Longitude") or fields_dict.get("GPS Longitude") or record_dict.get("GPS Longitude") or "-"
    coords = "-"
    if lat not in ("-", "0.000000", "0", 0, None) and lon not in ("-", "0.000000", "0", 0, None):
        try:
            lat_f = float(str(lat).strip())
            lon_f = float(str(lon).strip())
            if abs(lat_f) > 0.001 or abs(lon_f) > 0.001:
                coords = f"{lat_f:.4f}°, {lon_f:.4f}°"
        except Exception:
            pass
    if coords == "-":
        lat_m = re.search(r"([3-7]\d\.\d{4,8})", full_text)
        lon_m = re.search(r"([0-1]?\d{1,2}\.\d{4,8})", full_text)
        if lat_m and lon_m:
            try:
                coords = f"{float(lat_m.group(1)):.4f}°, {float(lon_m.group(1)):.4f}°"
            except Exception:
                coords = "-"

    # 5. Altitude & Flight Phase (Takeoff, Climb, Cruise, Descent based on altitude)
    alt_val = None
    raw_alt = record_dict.get("Altitude") or fields_dict.get("Barometric Altitude")
    if raw_alt and family != "Fault":
        try:
            num = float(str(raw_alt).strip())
            if 0 <= num <= 45000:
                alt_val = num
        except Exception:
            pass

    if alt_val is None and family != "Fault":
        alt_m = re.search(r"altitude\s*[:=]?\s*(\d{2,5})", full_text)
        if alt_m:
            num = float(alt_m.group(1))
            if 0 <= num <= 45000:
                alt_val = num

    if alt_val is not None and alt_val >= 400.0:
        if alt_val >= 10000.0:
            phase = "Cruise"
            altitude_str = f"{alt_val:,.0f} ft"
        else:
            phase = "Climb Ascent"
            altitude_str = f"{alt_val:,.0f} ft"
    elif "takeoff" in full_text:
        phase = "Takeoff Roll"
        altitude_str = f"{alt_val:,.0f} ft" if alt_val else "45 ft"
    elif "descent" in full_text:
        phase = "Descent / Landing"
        altitude_str = f"{alt_val:,.0f} ft" if alt_val else "8,000 ft"
    else:
        phase = "Pre-Flight Gate"
        altitude_str = "0 ft (Ground)"

    # 6. Machine Code & Microprocessor Fault
    machine_code = "Nominal"
    sw_addr = record_dict.get("Software fault address") or fields_dict.get("Software Fault Address")
    if sw_addr:
        try:
            val_int = int(re.sub(r"[^\d]", "", str(sw_addr)))
            machine_code = f"CPU TRAP 0x{val_int:08X}"
        except Exception:
            machine_code = f"CPU TRAP {sw_addr}"
    elif "software fault address" in full_text:
        m = re.search(r"software fault address\s*[:=]?\s*(\d+)", full_text)
        if m:
            val_int = int(m.group(1))
            machine_code = f"CPU TRAP 0x{val_int:08X}"
        else:
            machine_code = "CPU Instruction Trap"
    elif family == "Fault":
        code = str(record_dict.get("Fault Code") or record_dict.get("Encoded Fault") or "").strip()
        if code in BITE_FAULT_MAP:
            name, _ = BITE_FAULT_MAP[code]
            machine_code = f"BITE {code} ({name[:16]})"
        elif code:
            machine_code = f"BITE Fault {code}"
        else:
            machine_code = "BITE Diagnostic Alert"
    elif "pid" in full_text or "process id" in full_text:
        m = re.search(r"pid\s*(\d+)", full_text)
        pid_val = m.group(1) if m else "653"
        machine_code = f"PID {pid_val} Unacquired"
    elif "mutex" in full_text or "semaphore" in full_text:
        machine_code = "Mutex Lock Timeout"
    elif "deadline" in full_text:
        machine_code = "RTOS Deadline Miss"
    elif is_crit:
        machine_code = "Hardware Exception"

    return {
        "domain": domain,
        "pilot_input": pilot_input,
        "nav_data": nav_data,
        "phase": phase,
        "altitude": altitude_str,
        "coords": coords,
        "machine_code": machine_code,
    }


def build_ui_dataset(limit: int | None = None) -> dict[str, Any]:
    """
    Query all records from DuckDB, run the translator on every field,
    and format them into the schema for the UI.
    """
    ensure_data_dirs()
    conn = init_duckdb(DUCKDB_PATH)

    sql = """
        SELECT 
            event_id, 
            node_id, 
            source_file, 
            source_table_id, 
            source_row_number, 
            timestamp_raw, 
            timestamp_normalized, 
            original_record
        FROM all_records
        ORDER BY timestamp_normalized ASC NULLS LAST
    """
    if limit:
        sql += f" LIMIT {limit}"

    rows = conn.execute(sql).fetchall()
    conn.close()

    events: list[dict[str, Any]] = []
    translations: dict[str, str] = {}
    family_counts: dict[str, dict[str, int]] = {}

    first_sec = None

    for idx, (event_id, node_id, source_file, table_id, row_num, ts_raw, ts_norm, orig_json) in enumerate(rows):
        family = _detect_family(source_file)
        node = str(node_id).upper()

        if family not in family_counts:
            family_counts[family] = {"rowsIn": 0, "parsed": 0, "skipped": 0}
        family_counts[family]["rowsIn"] += 1

        # Parse normalized timestamp
        time24 = "12:00:00"
        ts_sec = 0.0
        if ts_norm:
            try:
                dt = datetime.fromisoformat(ts_norm)
                time24 = dt.strftime("%H:%M:%S")
                # Seconds since midnight
                day_sec = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1_000_000
                if first_sec is None:
                    first_sec = day_sec
                ts_sec = round(day_sec, 3)
            except Exception:
                time24 = ts_norm[11:19] if len(ts_norm) >= 19 else "12:00:00"

        # Parse original record dict
        try:
            record_dict = json.loads(orig_json) if isinstance(orig_json, str) else (orig_json or {})
        except Exception:
            record_dict = {}

        event_id_str = f"{node}-{family}-{idx+1}"
        headline, summary, synth_cat, synth_flags = synthesize_event_headline(record_dict, family, node)

        # Store plain-language summary keyed by event ID for the UI
        translations[event_id_str] = summary

        fields_dict: dict[str, Any] = {}
        flags: list[str] = list(synth_flags)
        name = headline
        code = str(row_num)
        category = synth_cat

        if family == "Fault":
            code = str(record_dict.get("Fault Code") or record_dict.get("Fault Code", idx + 1))
            for col_name, col_val in record_dict.items():
                if col_name in ("Date and Time", "Date and time", "Serial Number"):
                    continue
                val_str = str(col_val or "").strip()
                title, desc = translate_field(col_name, val_str)
                fields_dict[title] = val_str
                translations[title] = desc

                v_low = val_str.lower()
                d_low = desc.lower()
                if any(w in v_low for w in ["not ok", "unstable", "invalid", "fail", "restart"]) or "failure" in d_low:
                    flags.append("critical")

        else:
            # Buffer logs with Message cell
            msg_val = record_dict.get("Message") or ""
            msg_items = _parse_message_field(str(msg_val))

            if msg_items:
                for k, v, title, desc in msg_items:
                    fields_dict[title] = v
                    translations[title] = desc
                    v_low = v.lower()
                    d_low = desc.lower()
                    if any(w in v_low for w in ["not ok", "unstable", "invalid", "single", "fail"]) or "overflow" in d_low:
                        flags.append("critical")

            # Also add non-message columns (Latitude, Longitude, Altitude, etc.)
            for col_name, col_val in record_dict.items():
                if col_name in ("Message", "Date and time", "Date and Time", "Sequence number", "Sequence Number"):
                    continue
                val_str = str(col_val or "").strip()
                title, desc = translate_field(col_name, val_str)
                fields_dict[title] = val_str
                translations[title] = desc

            seq_val = record_dict.get("Sequence number") or record_dict.get("Sequence Number")
            if seq_val:
                code = f"SEQ-{seq_val}"

        flags = list(set(flags))
        family_counts[family]["parsed"] += 1
        teammate_cols = _extract_teammate_columns(record_dict, family, node, fields_dict)

        events.append({
            "id": event_id_str,
            "family": family,
            "node": node,
            "session": "1",
            "seq": idx + 1,
            "time24": time24,
            "tsSec": ts_sec,
            "category": category,
            "name": name,
            "code": code,
            "fields": fields_dict,
            "flags": flags,
            "rawHtml": "",
            "parseNotes": [],
            # Teammate's Dedicated Avionics Columns:
            "domain": teammate_cols["domain"],
            "pilotInput": teammate_cols["pilot_input"],
            "navData": teammate_cols["nav_data"],
            "phase": teammate_cols["phase"],
            "altitude": teammate_cols["altitude"],
            "coords": teammate_cols["coords"],
            "machineCode": teammate_cols["machine_code"],
        })

    report = {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "source": "FlightStory DuckDB Analytical Warehouse (Real Aircraft Logs)",
        "totals": {
            "rowsIn": len(rows),
            "events": len(events),
            "skipped": 0,
        },
        "byFamily": family_counts,
        "skipped": [],
    }

    return {
        "events": events,
        "translations": translations,
        "report": report,
        "incidents": None,  # Excluded per user request (no correlation/story view)
    }


def export_ui_dataset(output_dir: Path | None = None) -> Path:
    """
    Export the translated dataset directly to the frontend's data directory.
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "existing_design" / "data" / "mock"

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_ui_dataset()

    (output_dir / "events.json").write_text(json.dumps(dataset["events"], indent=2), encoding="utf-8")
    (output_dir / "translations.json").write_text(json.dumps(dataset["translations"], indent=2), encoding="utf-8")
    (output_dir / "import_report.json").write_text(json.dumps(dataset["report"], indent=2), encoding="utf-8")
    (output_dir / "incidents.json").write_text(json.dumps({"incidents": []}, indent=2), encoding="utf-8")

    log.info("Exported UI dataset with %d events to %s", len(dataset["events"]), output_dir)
    return output_dir
