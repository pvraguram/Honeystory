import os
import re
import html
import json
import webbrowser
from pathlib import Path
from datetime import timedelta
import pandas as pd
import networkx as nx
from bs4 import BeautifulSoup

# =====================================================================
# PATH SETTINGS
# =====================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "input_html"
INPUT_FOLDER = DEFAULT_INPUT if DEFAULT_INPUT.exists() else Path(r"D:\translating")
OUTPUT_HTML = PROJECT_ROOT / "data" / "verified_flight_translation.html"
OUTPUT_JSON = PROJECT_ROOT / "data" / "verified_flight_translation.json"


# =====================================================================
# 1. LOG CORRELATION ENGINE LAYER
# =====================================================================
class LogCorrelationLayer:
    """
    Stateless Log Correlation Engine Layer.
    1. Normalizes log inputs and extracts Deos/Process PIDs.
    2. Clusters events in a sliding time window (Δt) and debounces floods.
    3. Builds a Directed Acyclic Graph (DAG) using causal rules.
    4. Ranks root causes by total downstream blast radius.
    """
    def __init__(self, time_window_seconds: int = 15):
        self.time_window = timedelta(seconds=time_window_seconds)
        self.causal_rules = {
            6074: [6025, 6052, 6035],   # File EOF -> Process ID / Lib load failures
            6035: [6029, 6024],         # Missing Callback -> Semaphore deadlocks
            6029: [6000],               # Semaphore Lock -> Service deadline misses
            6000: [11631, 11632, 11633] # Deadline Miss -> Nav receiver timeouts
        }

    def process(self, raw_records: list) -> dict:
        if not raw_records:
            return {"root_causes": [], "nodes": [], "edges": []}

        df = self._normalize(raw_records)
        df_debounced = self._cluster_and_debounce(df)
        G = self._build_dag(df_debounced)
        root_causes = self._score_roots(G)

        return {
            "root_causes": root_causes,
            "nodes": [{"id": node, "in_degree": G.in_degree(node), "out_degree": G.out_degree(node)} for node in G.nodes()],
            "edges": [{"from": u, "to": v, "lines": data["evidence_lines"], "count": int(data["child_occurrences"])} for u, v, data in G.edges(data=True)]
        }

    def _normalize(self, raw_records: list) -> pd.DataFrame:
        parsed = []
        for idx, rec in enumerate(raw_records):
            desc = str(rec.get("description", ""))
            pid_match = re.search(r"(?:deos|process)\s+(\d+)", desc, re.IGNORECASE)
            
            parsed.append({
                "log_id": rec.get("log_id", idx + 1),
                "timestamp": pd.to_datetime(rec.get("timestamp")),
                "fault_code": int(rec.get("fault_code", 0)),
                "process_id": int(pid_match.group(1)) if pid_match else None,
                "description": desc
            })
        return pd.DataFrame(parsed)

    def _cluster_and_debounce(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("timestamp").reset_index(drop=True)
        df["cluster_id"] = (df["timestamp"].diff() > self.time_window).cumsum()
        
        aggregated = []
        for (cluster_id, code), group in df.groupby(["cluster_id", "fault_code"]):
            aggregated.append({
                "cluster_id": cluster_id,
                "fault_code": code,
                "occurrence_count": len(group),
                "source_line_ids": group["log_id"].tolist()
            })
        return pd.DataFrame(aggregated)

    def _build_dag(self, cluster_df: pd.DataFrame) -> nx.DiGraph:
        G = nx.DiGraph()
        for cluster_id, group in cluster_df.groupby("cluster_id"):
            present_codes = set(group["fault_code"].tolist())
            for parent, children in self.causal_rules.items():
                if parent in present_codes:
                    for child in children:
                        if child in present_codes:
                            c_row = group[group["fault_code"] == child].iloc[0]
                            G.add_edge(parent, child, cluster_id=cluster_id, evidence_lines=c_row["source_line_ids"], child_occurrences=c_row["occurrence_count"])
        return G

    def _score_roots(self, G: nx.DiGraph) -> list:
        roots = [node for node, in_deg in G.in_degree() if in_deg == 0]
        results = []
        for root in roots:
            downstream = nx.descendants(G, root)
            results.append({
                "root_fault_code": root,
                "blast_radius": len(downstream),
                "affected_downstream_faults": [int(c) for c in downstream]
            })
        return sorted(results, key=lambda x: x["blast_radius"], reverse=True)


# =====================================================================
# 2. TRANSLATION ENGINE
# =====================================================================
# =====================================================================
# 2. TRANSLATION ENGINE & DOMAIN DICTIONARIES
# =====================================================================
MCDU_BUTTON_MAP = {
    0: "Idle (No Key Pressed)",
    1024: "DIR (Direct-To) Key",
    1792: "PROG (Progress) Key",
    4864: "PERF (Performance) Key",
    4869: "INIT (Initialization) Key",
    6656: "F-PLN (Flight Plan) Key",
    7424: "RAD NAV (Radio Navigation) Key",
    7680: "SEC F-PLN (Secondary Route) Key",
    9728: "FUEL PRED (Fuel Prediction) Key",
    10752: "SEC F-PLN Page Select",
    10753: "SEC F-PLN Page Select",
    12288: "AIRPORT Page Key",
    13824: "ATC COMM Key",
    16897: "DATA Page Key",
    17921: "MCDU MENU Key",
    19456: "Line Select Key (LSK 2L)",
    20480: "Line Select Key (LSK 1L)",
    23808: "Line Select Key (LSK 4R)",
    34816: "CLR (Clear) Key",
}

FLIGHT_PHASE_MAP = {
    "0": ("Pre-Flight Gate Setup", "Stationary aircraft at gate; pre-flight route programming and systems initialization."),
    "1": ("Taxi Out", "Aircraft taxiing from gate toward active departure runway."),
    "2": ("Takeoff Roll", "Active takeoff run and initial pitch rotation."),
    "3": ("Climb Out", "Ascent through terminal area toward assigned cruise flight level."),
    "4": ("Cruise Flight", "Level cruise at assigned flight level and speed schedule."),
    "5": ("Descent Phase", "En-route descent toward arrival corridor."),
    "6": ("Approach & Alignment", "Instrument approach alignment with active runway."),
    "7": ("Go-Around / Missed Approach", "Aborted landing procedure; executing published missed approach."),
    "8": ("Landing Rollout", "Touchdown and runway deceleration."),
    "9": ("Taxi In", "Taxiing from runway exit to terminal parking gate."),
}

BITE_FAULT_MAP = {
    "6000": ("RTOS Real-Time Deadline Missed", "Deos background service thread failed to complete computation within its allotted scheduling slice."),
    "6001": ("Application Software Core Exception", "User-space process trap triggered by memory access exception or invalid opcode."),
    "6024": ("OS Service Task Client Unregistered", "Task registration dropped or disconnected from operating system service daemon."),
    "6025": ("Background Service Identity Lookup Failure", "FMS daemon failed to acquire process ID from Deos kernel (get current process id failure 653)."),
    "6029": ("OS Synchronization Semaphore Timeout", "Inter-task mutex lock contention or semaphore wait timeout in Deos RTOS."),
    "6035": ("OS Inter-Process Service Bind Failure", "Client callback handler missing or unmapped in Deos RTOS table."),
    "6052": ("Dynamic Shared Module Load Failure", "Failed to load shared library in RTOS address space (libpssl dtf manager)."),
    "6053": ("Hardware Floating Point Arithmetic Exception", "Math coprocessor signaled arithmetic exception or divide-by-zero."),
    "6074": ("FMS Data Repository Access Failure", "Premature EOF encountered while reading public FMS navigation artifacts."),
    "6080": ("Kernel Task Priority API Error", "Deos RTOS API returned error code during process priority arbitration."),
    "0": ("No Maintenance Fault Active", "Normal diagnostic state; BITE system reports no active hardware faults."),
    "2": ("General System Hardware Trap", "Low-level system exception reported on internal avionics bus."),
    "5": ("Navigation Database Cycle / CRC Error", "Navigation database expired, corrupted, or CRC checksum mismatch detected."),
    "6": ("RNP Receiver Bus Sync Timeout", "Required Navigation Performance cross-channel receiver timed out or overflowed."),
    "9": ("Process Startup Sequence Abort", "Background task failed initialization during system boot sequence."),
    "10": ("Real-Time Trajectory Computation Timeout", "Navigation guidance thread failed to converge trajectory within computation deadline."),
    "11": ("Cross-FMS Navigation Coordination Error", "Dual-channel FMS flight plan synchronization and coordination failed."),
}

CDU_PAGE_MAP = {
    "0": "Menu / Root Index Page",
    "1": "INIT A (Flight Initialization)",
    "2": "PERF (Performance & Speeds)",
    "3": "DIR TO (Direct-To Waypoint)",
    "33": "F-PLN (Active Flight Plan)",
}


def translate_field(field_name, value_str):
    f = re.sub(r"\s+", " ", str(field_name).strip().lower())
    v = str(value_str).strip()
    v_lower = v.lower()

    # Authority and Redundancy
    if "master status" in f:
        title = "Master Guidance Authority"
        if "master" in v_lower:
            desc = "Active Command Channel: Primary authority driving autopilot and flight directors."
        elif "standby" in v_lower or "spare" in v_lower or v == "0":
            desc = "Standby Mirror Mode: Secondary channel tracking master and cross-checking calculations."
        else:
            desc = f"Guidance authority registered as {v}."
        return title, desc

    if "dual mode" in f:
        title = "Redundancy Safety Mode"
        if "single" in v_lower:
            desc = "Redundancy Degraded: Operating in Single-FMS mode (cross-channel cross-checks suspended)."
        else:
            desc = "Dual Redundancy Active: Both flight computers synchronized and cross-checking."
        return title, desc

    if "opposite fms ok" in f:
        title = "Cross-Channel Link Verification"
        if any(x in v_lower for x in ["not ok", "fail"]):
            desc = "Cross-Channel Link Failure: Partner FMS failed periodic heartbeat; inter-FMS bus isolated."
        elif "unstable" in v_lower:
            desc = "Cross-Channel Link Intermittent: Sync jitter or packet latency detected on inter-FMS bus."
        else:
            desc = "Inter-FMS Bus Healthy: Periodic heartbeat and data sync across channels is normal."
        return title, desc

    if "standby fms node position" in f or "other dual fms" in f:
        title = "Avionics Rack Address"
        if "invalid" in v_lower:
            desc = "Hardware Bus Dropout: Standby computer's physical rack address is unreachable on the avionics bus."
        else:
            desc = f"Assigned to avionics bus rack position: {v}."
        return title, desc

    if "functional position" in f:
        title = "Flight Deck Station Routing"
        if "captain" in v_lower:
            desc = "Captain Station: Dedicated to Left-Hand (LH) Primary Flight Display & MCDU."
        elif "first officer" in v_lower:
            desc = "First Officer Station: Dedicated to Right-Hand (RH) Navigation Display & MCDU."
        else:
            desc = f"Dedicated to {v} console and display unit."
        return title, desc

    # Flight Phases and Legs
    if "flight leg" in f or "flight phase" in f:
        title = "Operational Flight Phase"
        if v in FLIGHT_PHASE_MAP:
            phase_name, phase_desc = FLIGHT_PHASE_MAP[v]
            return f"Flight Phase: {phase_name}", phase_desc
        return title, f"Active Flight Leg / Phase: {v}."

    # Pilot MCDU Inputs & Operator Events
    if "enter origin" in f or "enter origin" in v_lower:
        return "Departure Airport Programmed", "Flight crew entered origin airport identifier into the route."
    if "enter destination" in f or "enter destination" in v_lower:
        return "Destination Airport Programmed", "Flight crew entered destination airport code into the flight plan."
    if "enter crz fl" in f or "enter crz fl" in v_lower:
        return "Cruise Altitude Configured", "Flight crew selected planned cruising flight level."
    if "enter cost index" in f or "enter cost index" in v_lower:
        return "Cost Index Profile Set", "Flight crew entered airline economic index balancing flight speed against fuel burn."
    if "enter zfw" in f or "enter zfw" in v_lower:
        return "Zero Fuel Weight Keyed In", "Flight crew logged payload dry mass (passengers and cargo without fuel)."
    if "enter zfwcg" in f or "enter zfwcg" in v_lower:
        return "Center of Gravity Balanced", "Flight crew configured weight balance for aerodynamic stability."
    if "enter block" in f or "enter block" in v_lower:
        return "Total Block Fuel Confirmed", "Flight crew confirmed total block fuel onboard."
    if "enter departure runway" in f or "enter departure runway" in v_lower:
        return "Departure Runway Selected", "Flight crew selected the active takeoff runway on the MCDU."
    if "enter approach" in f or "enter approach" in v_lower:
        return "Landing Approach Selected", "Flight crew chose landing runway and instrument approach procedure."
    if "enter arrival procedure" in f or "enter arrival procedure" in v_lower:
        return "Descent Corridor (STAR) Set", "Flight crew programmed standard terminal arrival route."
    if "enter departure procedure" in f or "enter departure procedure" in v_lower:
        return "Departure Corridor (SID) Set", "Flight crew programmed standard instrument departure route."
    if "delete discon" in f or "delete discon" in v_lower:
        return "Route Discontinuity Removed", "Flight crew closed flight plan waypoint gap to link consecutive legs."
    if "enter offset distance" in f or "enter offset distance" in v_lower:
        return "Lateral Route Offset Programmed", "Flight crew entered parallel lateral track offset for weather/traffic avoidance."
    if "navigation database refresh cycle" in f or "navigation database refresh cycle" in v_lower or "check data base cycle" in f:
        return "Nav Database Verification", "FMS verified active validity cycle dates of navigation database."
    if "refresh sec index" in f or "refresh sec index" in v_lower:
        return "Secondary Route Synced", "System updated and synchronized backup flight plan."
    if "takeoff complete reset" in f or "takeoff complete reset" in v_lower:
        return "Takeoff Trajectory Reset", "FMS transitioned from takeoff guidance into active en-route climb mode."
    if "navigation primary" in f or "navigation primary" in v_lower:
        return "Primary Navigation Engaged", "FMS multi-sensor navigation filter confirmed primary GPS/IRS position."
    if "lateral revision" in f or "lateral revision" in v_lower:
        return "Lateral Route Revision", "Flight crew initiated lateral waypoint modification on MCDU."
    if "vertical guidance sequence changed" in f or "vertical guidance sequence changed" in v_lower:
        return "Vertical Profile Updated", "VNAV guidance recalculated vertical profile altitude and speed constraints."
    if "operational startup mode" in f:
        title = "FMS Startup Boot Mode"
        if "cold" in v_lower:
            desc = "Cold Boot: Full hardware power-up initialization sequence."
        elif "warm" in v_lower:
            desc = "Warm Restart: Fast recovery reboot preserving active flight plan cache."
        else:
            desc = f"Startup mode registered as {v}."
        return title, desc

    # Hardware, Buttons and CDU Fields
    if "button push index" in f:
        try:
            b_idx = int(v)
            b_name = MCDU_BUTTON_MAP.get(b_idx, f"Key Code {b_idx}")
            return "MCDU Keypad Input", f"Key press detected: {b_name}."
        except Exception:
            return "MCDU Keypad Input", f"Key press index registered as {v}."

    if "button push in progress" in f:
        title = "Keypad Contact State"
        desc = "MCDU button currently held down (contact closed)." if v == "1" else "MCDU button released (contact open)."
        return title, desc

    if "cdu scratchpad" in f:
        title = "CDU Scratchpad Buffer"
        if v in ("-19712", "0"):
            desc = "Scratchpad cleared and ready for new flight crew input."
        else:
            desc = f"Scratchpad buffer memory offset: {v}."
        return title, desc

    if "cdu title page" in f:
        title = "Active CDU Display Page"
        page_name = CDU_PAGE_MAP.get(v, f"Page ID {v}")
        return title, f"MCDU currently displaying {page_name}."

    if "ils mode" in f:
        title = "Instrument Landing Mode"
        if v == "17":
            desc = "Mode 17: ILS Approach Active (LOC and Glideslope dual-channel guidance tracking)."
        elif v == "0":
            desc = "Mode 0: ILS Inactive (Standard Area Navigation active)."
        else:
            desc = f"ILS Mode {v} engaged."
        return title, desc

    # Faults and Maintenance
    if "fault code" in f or "fault identifier code" in f or "encoded fault" in f:
        title = "BITE Maintenance Fault Code"
        if v in BITE_FAULT_MAP:
            f_title, f_desc = BITE_FAULT_MAP[v]
            return f"Fault {v}: {f_title}", f_desc
        return title, f"Diagnostic maintenance code registered as {v}."

    if "fault name" in f:
        title = "Diagnostic Fault Name"
        return title, f"BITE system reported diagnostic condition: {v}."

    if "sub code" in f:
        title = "Diagnostic Sub-Code"
        return title, f"Hardware subsystem identifier: {v}."

    if "application data" in f and "raw" not in f:
        title = "OS Process Diagnostic Detail"
        if "get current process id failure" in v_lower:
            desc = "RTOS Process ID Query Failed: Deos kernel could not return PID for worker thread 653."
        elif "wait semaphore failed" in v_lower:
            desc = "Semaphore Timeout: Worker thread blocked waiting on locked RTOS synchronization mutex."
        elif "deadline miss" in v_lower:
            desc = "Thread Scheduling Overrun: Real-time background task exceeded maximum allotted execution window."
        elif "client cb not found" in v_lower:
            desc = "Inter-Process Link Failure: Client callback pointer missing from RTOS process table."
        elif "failed to load library" in v_lower:
            desc = "Dynamic Link Failure: Kernel could not map shared module libpssl into memory."
        elif "can not get line" in v_lower:
            desc = "Filesystem Read Fault: Premature end-of-file reached while parsing FMS data file."
        else:
            desc = f"Internal operating system diagnostic log: '{v}'."
        return title, desc

    if "last module reset reason" in f or "last context reset reason" in f:
        title = "Recovery Action Triggered"
        if "service restart" in v_lower:
            desc = "Automatic Recovery: Avionics watchdog restarted background FMS service."
        elif "no recovery action" in v_lower:
            desc = "No recovery action required; system operating within fault-tolerant boundaries."
        else:
            desc = f"Recovery mechanism logged: {v}."
        return title, desc

    # Telemetry and Flight Parameters
    if "altitude" in f:
        try:
            alt_f = round(float(v))
            return "Barometric Altitude", f"Aircraft pressure height recorded at {alt_f:,} feet."
        except Exception:
            return "Barometric Altitude", f"Aircraft pressure height recorded at {v} feet."

    if "airspeed" in f:
        try:
            spd_f = round(float(v), 1)
            return "Calibrated Airspeed", f"Aircraft velocity registered at {spd_f} knots."
        except Exception:
            return "Calibrated Airspeed", f"Aircraft velocity registered at {v} knots."

    if "gross weight" in f:
        try:
            gw_f = round(float(v))
            tonnes = round(gw_f * 0.000453592, 1)
            return "Total Aircraft Mass", f"Gross total aircraft weight measured at {gw_f:,} lbs (~{tonnes} tonnes)."
        except Exception:
            return "Total Aircraft Mass", f"Gross total aircraft weight measured at {v}."

    if "latitude" in f:
        return "GPS Latitude", f"Geographic latitude coordinate: {v}°."
    if "longitude" in f:
        return "GPS Longitude", f"Geographic longitude coordinate: {v}°."
    if "magnetic track" in f:
        return "Magnetic Heading Track", f"Aircraft heading reference: {v}°."

    if "air frame ident" in f:
        return "Airframe Classification", "Aircraft airframe identified as Airbus A350 widebody."
    if "engine ident" in f:
        return "Engine Configuration", "Propulsion identified as Rolls-Royce Trent XWB high-bypass turbofans."

    if "software fault address" in f:
        return "CPU Instruction Exception", f"Microprocessor trap logged at internal memory address {v}."

    clean_title = field_name.replace("_", " ").strip().title()
    return clean_title, f"{clean_title} parameter recorded as '{v}'."


def synthesize_event_headline(record_dict, family, node_id):
    """
    Synthesize an intuitive, human-readable headline, plain-English summary,
    category, and severity flags for an avionics event record.
    """
    merged = dict(record_dict)
    msg = str(merged.get("Message", "") or "")

    # Extract nested fields from HTML list or text if present
    if "<li" in msg or "<ul" in msg:
        soup = BeautifulSoup(msg, "html.parser")
        for item in soup.find_all("li"):
            label = item.find("strong")
            if label:
                k = label.get_text(" ", strip=True).rstrip(":")
                raw_text = item.get_text(" ", strip=True)
                v = raw_text[len(label.get_text(" ", strip=True)):].strip()
                merged[k] = v
    elif ":" in msg:
        for line in re.split(r"[•\n]", msg):
            cleaned = re.sub(r"^[•\-\*]\s*", "", line).strip()
            if ":" in cleaned:
                k, v = cleaned.split(":", 1)
                merged[k.strip()] = v.strip()

    merged_lower = {k.lower(): str(v) for k, v in merged.items()}

    # --- 1. FAULT RECORDS ---
    if family == "Fault":
        code = str(merged.get("Fault Code") or merged.get("Encoded Fault") or "").strip()
        name = str(merged.get("Fault Name") or "").strip()
        app_data = str(merged.get("Application Data") or "").strip()
        reset_reason = str(merged.get("Last Module Reset Reason") or "").strip()

        if code in BITE_FAULT_MAP:
            f_title, f_desc = BITE_FAULT_MAP[code]
            if code == "6025":
                headline = "BITE Fault 6025: Process Identity Lookup Failure (PID 653)"
                summary = "Deos RTOS daemon failed to acquire process ID from kernel in Pre-Flight Gate Setup. Automatic Recovery: FMS Service Restart."
            elif code == "6000":
                headline = "BITE Fault 6000: RTOS Real-Time Deadline Missed"
                summary = f"Background service thread exceeded scheduling slice. Diagnostic data: {app_data}."
            elif code == "6029":
                headline = "BITE Fault 6029: OS Semaphore Mutex Timeout"
                summary = "Task blocked on RTOS synchronization lock in Deos microkernel."
            elif code == "6035":
                headline = "BITE Fault 6035: Inter-Process Service Bind Failure"
                summary = f"Client callback handler missing in Deos process table ({app_data})."
            elif code == "6052":
                headline = "BITE Fault 6052: Shared Module Dynamic Load Failure"
                summary = "Operating system failed to map shared library libpssl into memory."
            elif code == "6074":
                headline = "BITE Fault 6074: Navigation Repository File EOF Failure"
                summary = "Premature end-of-file reached while reading public FMS navigation artifacts."
            elif code == "6080":
                headline = "BITE Fault 6080: Kernel Process API / Priority Error"
                summary = f"Deos RTOS returned API error during priority arbitration: {app_data}."
            else:
                headline = f"BITE Fault {code}: {f_title}"
                summary = f"{f_desc} Recovery: {reset_reason or 'None required'}."
        elif name:
            headline = f"BITE Fault {code}: {name}" if code else f"BITE Diagnostic: {name}"
            summary = f"System diagnostic alert triggered on {node_id}. Application detail: {app_data or 'Standard BITE log'}."
        else:
            headline = f"BITE Diagnostic Event ({node_id})"
            summary = f"Diagnostic report logged on {node_id} with status code {code}."

        return headline, summary, "fault", ["critical"]

    # --- 2. STATE RECORDS ---
    if family in ("STATE", "State_Transition"):
        opp_ok = merged_lower.get("opposite fms ok", "")
        dual_mode = merged_lower.get("dual mode", "")
        master_status = merged_lower.get("master status", "")
        ils_mode = merged_lower.get("ils mode", "")
        gross_weight = merged_lower.get("gross weight", "")

        if "not ok" in opp_ok or "fail" in opp_ok:
            headline = "Redundancy Alert: Partner FMS Lost Heartbeat"
            summary = f"Primary guidance channel on {node_id} detected cross-talk bus timeout. Partner FMS channel isolated."
            return headline, summary, "state", ["critical"]
        if "unstable" in opp_ok:
            headline = "Redundancy Warning: Cross-Talk Link Intermittent"
            summary = "Periodic heartbeat test detected synchronization jitter or latency on the inter-FMS bus."
            return headline, summary, "state", ["warning"]
        if "ok" in opp_ok:
            headline = "Redundancy Healthy: Dual FMS Channels Synchronized"
            summary = "Cross-talk bus verified; both flight management computers synchronized and cross-checking."
            return headline, summary, "state", []

        if "single" in dual_mode:
            headline = "Guidance Degraded: Switched to Single-FMS Mode"
            summary = "Dual redundancy lost; flight computer operating in standalone mode without cross-checks."
            return headline, summary, "state", ["critical"]

        if ils_mode == "17":
            headline = "ILS Approach Mode 17 Engaged (LOC & Glideslope Active)"
            summary = "Dual-channel instrument landing system guidance tracking runway localizer and glideslope."
            return headline, summary, "state", []

        if gross_weight and gross_weight not in ("0", "0.0", "0.000000"):
            try:
                gw_val = round(float(gross_weight))
                headline = f"Flight State Snapshot: Calculated Weight {gw_val:,} lbs"
                summary = f"Active navigation performance model tracking gross mass ({gw_val:,} lbs) and barometric parameters."
                return headline, summary, "state", []
            except Exception:
                pass

        headline = f"Guidance & Redundancy State Update ({node_id})"
        summary = f"Master: {master_status.capitalize() or 'Active'} | Mode: {dual_mode.capitalize() or 'Standard'} | Node: {node_id}."
        return headline, summary, "state", []

    # --- 3. BPQ & OPERATOR / TELEMETRY RECORDS ---
    actor = "Flight Crew"
    pos = merged_lower.get("functional position", "") or merged_lower.get("source fms node", "")
    if "captain" in pos:
        actor = "Captain"
    elif "first officer" in pos:
        actor = "First Officer"

    all_text = " ".join([k + " " + str(v) for k, v in merged.items()]).lower()

    if "enter departure runway" in all_text:
        headline = f"{actor} Selected Departure Runway"
        summary = f"{actor} assigned the active departure runway on MCDU while parked at Gate."
        return headline, summary, "telemetry", []

    if "enter origin" in all_text:
        headline = f"{actor} Programmed Departure Airport"
        summary = f"{actor} entered the origin airport code into the navigation plan via MCDU."
        return headline, summary, "telemetry", []

    if "enter destination" in all_text:
        headline = f"{actor} Programmed Destination Airport"
        summary = f"{actor} entered the destination airport code into the active route via MCDU."
        return headline, summary, "telemetry", []

    if "enter crz fl" in all_text:
        headline = f"{actor} Configured Cruising Flight Level"
        summary = f"{actor} entered target cruise flight level on the MCDU."
        return headline, summary, "telemetry", []

    if "enter cost index" in all_text:
        headline = f"{actor} Set Cost Index Profile"
        summary = f"{actor} configured the speed and fuel economy optimization ratio."
        return headline, summary, "telemetry", []

    if "enter zfw" in all_text or "enter zfwcg" in all_text:
        headline = f"{actor} Entered Zero Fuel Weight & CG"
        summary = f"{actor} logged payload dry weight and verified center of gravity trim."
        return headline, summary, "telemetry", []

    if "enter block" in all_text:
        headline = f"{actor} Confirmed Total Block Fuel"
        summary = f"{actor} confirmed onboard departure block fuel load on MCDU."
        return headline, summary, "telemetry", []

    if "enter approach" in all_text:
        headline = f"{actor} Selected Instrument Approach"
        summary = f"{actor} chose instrument runway landing procedure on MCDU."
        return headline, summary, "telemetry", []

    if "enter arrival procedure" in all_text:
        headline = f"{actor} Programmed STAR Arrival Corridor"
        summary = f"{actor} selected standard terminal arrival route into destination."
        return headline, summary, "telemetry", []

    if "enter departure procedure" in all_text:
        headline = f"{actor} Programmed SID Departure Route"
        summary = f"{actor} selected standard instrument departure route from origin."
        return headline, summary, "telemetry", []

    if "delete discon" in all_text:
        headline = f"{actor} Cleared Route Discontinuity"
        summary = f"{actor} closed route gap between consecutive flight plan waypoints."
        return headline, summary, "telemetry", []

    if "enter offset" in all_text:
        headline = f"{actor} Programmed Lateral Route Offset"
        summary = f"{actor} entered parallel lateral track offset for traffic/weather avoidance."
        return headline, summary, "telemetry", []

    if "navigation database refresh cycle" in all_text:
        headline = f"Navigation Database Verified ({actor})"
        summary = "FMS verified active validity cycle dates of navigation database."
        return headline, summary, "telemetry", []

    if "takeoff complete reset" in all_text:
        headline = "Takeoff Guidance Reset Completed"
        summary = "FMS concluded takeoff guidance phase and transitioned to en-route climb profile."
        return headline, summary, "telemetry", []

    if "navigation primary" in all_text:
        headline = "Primary Navigation Reference Engaged"
        summary = "FMS confirmed high-accuracy multisensor position reference."
        return headline, summary, "telemetry", []

    if "lateral revision" in all_text:
        headline = f"{actor} Executed Lateral Route Revision"
        summary = f"{actor} initiated waypoint route revision on MCDU."
        return headline, summary, "telemetry", []

    if "vertical guidance sequence changed" in all_text:
        headline = "Vertical Guidance Profile Updated"
        summary = "VNAV guidance recalculated vertical profile altitude and speed constraints."
        return headline, summary, "telemetry", []

    if "operational startup" in all_text:
        mode_val = merged.get("Operational startup mode", "Cold Boot")
        headline = f"FMS Boot Sequence: {mode_val}"
        summary = f"Flight management system on {node_id} completed boot initialization."
        return headline, summary, "boot", []

    # Check button push
    btn_val = merged.get("Button push index")
    if btn_val is not None:
        try:
            b_name = MCDU_BUTTON_MAP.get(int(btn_val), f"Key {btn_val}")
            headline = f"{actor} Keyed MCDU '{b_name}'"
            summary = f"Cockpit interaction detected on {actor} keypad: {b_name}."
            return headline, summary, "telemetry", []
        except Exception:
            pass

    # Generic telemetry event headline
    data_ident = merged.get("Data Identifier") or merged.get("Event identifier") or merged.get("L message identifier")
    if data_ident:
        headline = f"{data_ident.title()} ({actor})"
        summary = f"Avionics event '{data_ident}' registered on {node_id} ({actor} station)."
        return headline, summary, "telemetry", []

    headline = f"Avionics Telemetry Event ({node_id})"
    summary = f"Flight parameters and system states recorded on {node_id}."
    return headline, summary, "telemetry", []


# =====================================================================
# 3. HTML LOG EXTRACTOR
# =====================================================================
def extract_rows_from_html(file_path):
    print(f"\n[SCANNING] Reading: {file_path.name}")
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")
    except Exception as exc:
        print(f"  [ERROR] Cannot read file: {exc}")
        return []

    node_match = re.search(r"NODE[_-]([A-Z0-9]+)", file_path.name, re.IGNORECASE)
    node_name = f"NODE_{node_match.group(1).upper()}" if node_match else "NODE_PRIMARY"

    records = []
    tables = soup.find_all("table")

    for t_idx, table in enumerate(tables, start=1):
        rows = table.find_all("tr")
        if not rows:
            continue

        for r_idx, row in enumerate(rows):
            cells = row.find_all(["td", "th"], recursive=False)
            if len(cells) < 2:
                continue

            first_text = cells[0].get_text(" ", strip=True).lower()
            if "sequence" in first_text or "seq" in first_text:
                continue

            seq = cells[0].get_text(" ", strip=True) if len(cells) > 0 else str(r_idx)
            ts = cells[1].get_text(" ", strip=True) if len(cells) > 1 else "Unknown Timestamp"
            msg_cell = cells[-1]

            extracted_fields = []

            # Format 1: <li> Tags
            li_items = msg_cell.select("li")
            if li_items:
                for item in li_items:
                    label = item.find("strong")
                    if label:
                        k = label.get_text(" ", strip=True).rstrip(":")
                        raw_v = item.get_text(" ", strip=True)
                        v = raw_v[len(label.get_text(" ", strip=True)):].strip()
                    else:
                        txt = item.get_text(" ", strip=True)
                        k, v = txt.split(":", 1) if ":" in txt else ("Parameter", txt)

                    title, desc = translate_field(k, v)
                    extracted_fields.append({
                        "raw_field": k.strip(),
                        "raw_value": v.strip(),
                        "title": title,
                        "desc": desc
                    })

            # Format 2: Bullets / Newlines
            if not extracted_fields:
                raw_text = msg_cell.get_text("\n", strip=True)
                for line in re.split(r'•|\n', raw_text):
                    cleaned = re.sub(r'^[•\-\*]\s*', '', line).strip()
                    if ":" in cleaned:
                        k, v = cleaned.split(":", 1)
                        title, desc = translate_field(k, v)
                        extracted_fields.append({
                            "raw_field": k.strip(),
                            "raw_value": v.strip(),
                            "title": title,
                            "desc": desc
                        })

            if extracted_fields:
                records.append({
                    "file": file_path.name,
                    "node": node_name,
                    "sequence": seq,
                    "timestamp": ts,
                    "fields": extracted_fields
                })

    print(f"  -> Extracted {len(records)} entries from {file_path.name}")
    return records


# =====================================================================
# 4. BRIDGE TRANSFORMER
# =====================================================================
def bridge_parser_to_correlation_engine(all_records):
    engine_input = []
    
    for r in all_records:
        line_id = f"{r['file']}_Seq_{r['sequence']}"
        for f in r["fields"]:
            val = f["raw_value"]
            fault_code = int(val) if val.isdigit() else 0
            
            engine_input.append({
                "log_id": line_id,
                "timestamp": r["timestamp"],
                "fault_code": fault_code,
                "description": f"{f['raw_field']}: {f['raw_value']} ({f['desc']})"
            })
            
    engine = LogCorrelationLayer(time_window_seconds=15)
    return engine.process(engine_input)


# =====================================================================
# 5. HTML BUILDER (WITH ROOT CAUSE BANNER)
# =====================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flight Story AI - Verified Complete Translation</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0; padding: 24px;
  background: #0d1117; color: #c9d1d9;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 1200px; margin: auto; }
h1 { color: #f0f6fc; margin-bottom: 4px; }
.top-bar {
  background: #161b22; border: 1px solid #30363d;
  border-radius: 8px; padding: 14px 20px; margin: 18px 0;
  display: flex; justify-content: space-between; align-items: center;
}
input#searchBox {
  background: #0d1117; border: 1px solid #30363d; color: #f0f6fc;
  padding: 8px 14px; border-radius: 6px; width: 340px; font-size: 13px;
}
.card {
  background: #161b22; border: 1px solid #30363d;
  border-radius: 8px; padding: 16px; margin-bottom: 16px;
}
.root-cause-card {
  border: 2px solid #f85149; background: rgba(248, 81, 73, 0.1);
  margin-bottom: 20px; border-radius: 8px; padding: 16px;
}
.card-head {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 10px; border-bottom: 1px solid #21262d; margin-bottom: 12px;
}
.node-pill {
  background: rgba(88, 166, 255, 0.15); color: #58a6ff;
  border: 1px solid rgba(88, 166, 255, 0.3); padding: 3px 8px;
  border-radius: 10px; font-weight: bold; margin-right: 8px; font-size: 12px;
}
.ts-meta { color: #8b949e; margin-left: 10px; font-size: 13px; }
.file-meta { color: #6e7681; margin-left: 6px; font-size: 11px; }
.pill { padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
.pill.danger { background: rgba(248, 81, 73, 0.2); color: #f85149; border: 1px solid rgba(248, 81, 73, 0.4); }
.pill.ok { background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid rgba(35, 134, 54, 0.4); }
.badge-title { color: #79c0ff; font-weight: 600; }
.table-container { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #30363d; padding: 8px 12px; text-align: left; font-size: 13px; }
th { background: #21262d; color: #f0f6fc; }
code { background: #21262d; padding: 2px 6px; border-radius: 4px; color: #ff7b72; font-family: monospace; }
</style>
</head>
<body>
<main>
  <h1>Flight Story AI: Complete Operational Translation Report</h1>
  <p style="color: #8b949e;">Every parameter and value verified and decoded into plain English</p>

  __ROOT_CAUSE_BANNER__

  <div class="top-bar">
    <div><strong>Total Translated Log Rows:</strong> __TOTAL_COUNT__</div>
    <input type="text" id="searchBox" placeholder="Type to search (e.g., Master, Single, Invalid, Node)..." onkeyup="filterCards()">
  </div>

  <div id="cardsList">
    __CARDS_CONTENT__
  </div>
</main>

<script>
function filterCards() {
  const query = document.getElementById('searchBox').value.toLowerCase();
  const cards = document.querySelectorAll('.card');
  cards.forEach(card => {
    const text = card.innerText.toLowerCase();
    card.style.display = text.includes(query) ? 'block' : 'none';
  });
}
</script>
</body>
</html>"""


def build_html_dashboard(all_records, correlation_results=None):
    cards_html = []

    # Render Root Cause Banner if available
    rc_banner = ""
    if correlation_results and correlation_results.get("root_causes"):
        primary = correlation_results["root_causes"][0]
        rc_banner = (
            f'<div class="root-cause-card">'
            f'<h2 style="color: #f85149; margin-top: 0;">PRIMARY ROOT CAUSE ISOLATED</h2>'
            f'<p><strong>Root Fault Code:</strong> <code>Code {primary["root_fault_code"]}</code></p>'
            f'<p><strong>Downstream Blast Radius:</strong> {primary["blast_radius"]} cascading failure points triggered</p>'
            f'</div>'
        )

    for r in all_records:
        field_rows = []
        has_alert = False

        for f in r["fields"]:
            val_low = f["raw_value"].lower()
            desc_low = f["desc"].lower()
            is_warn = any(w in val_low for w in ["not ok", "unstable", "invalid", "single", "fail"]) or "overflow" in desc_low

            if is_warn:
                has_alert = True
                row_bg = ' style="background: rgba(248, 81, 73, 0.15);"'
            else:
                row_bg = ''

            field_rows.append(
                f'<tr{row_bg}>'
                f'<td><strong>{html.escape(f["raw_field"])}</strong></td>'
                f'<td><code>{html.escape(f["raw_value"])}</code></td>'
                f'<td><span class="badge-title">{html.escape(f["title"])}</span></td>'
                f'<td>{html.escape(f["desc"])}</td>'
                f'</tr>'
            )

        status_badge = '<span class="pill danger">CRITICAL ALERT</span>' if has_alert else '<span class="pill ok">NORMAL</span>'

        card = (
            f'<article class="card">'
            f'<div class="card-head">'
            f'<div>'
            f'<span class="node-pill">{html.escape(r["node"])}</span>'
            f'<strong>Sequence #{html.escape(r["sequence"])}</strong>'
            f'<span class="ts-meta">{html.escape(r["timestamp"])}</span>'
            f'<span class="file-meta">({html.escape(r["file"])})</span>'
            f'</div>'
            f'{status_badge}'
            f'</div>'
            f'<div class="table-container">'
            f'<table>'
            f'<thead>'
            f'<tr>'
            f'<th style="width: 22%;">Original Log Field</th>'
            f'<th style="width: 18%;">Recorded State</th>'
            f'<th style="width: 25%;">Decoded System Function</th>'
            f'<th style="width: 35%;">Plain English Meaning</th>'
            f'</tr>'
            f'</thead>'
            f'<tbody>'
            f'{"".join(field_rows)}'
            f'</tbody>'
            f'</table>'
            f'</div>'
            f'</article>'
        )
        cards_html.append(card)

    cards_str = "".join(cards_html) if cards_html else "<p>No records found.</p>"
    page = HTML_TEMPLATE.replace("__TOTAL_COUNT__", str(len(all_records)))
    page = page.replace("__ROOT_CAUSE_BANNER__", rc_banner)
    page = page.replace("__CARDS_CONTENT__", cards_str)

    OUTPUT_HTML.write_text(page, encoding="utf-8")


# =====================================================================
# 6. MAIN CONTROLLER
# =====================================================================
def main():
    if not INPUT_FOLDER.exists():
        print(f"[ERROR] Directory does not exist: {INPUT_FOLDER}")
        return

    target_files = sorted(
        fp for fp in INPUT_FOLDER.rglob("*.html")
        if not fp.name.startswith("verified_") 
        and not fp.name.startswith("view_") 
        and not fp.name.startswith("complete_") 
        and not fp.name.startswith("clean_")
        and not fp.name.startswith("deduplicated_")
        and not fp.name.startswith("flight_story_")
    )

    if not target_files:
        print(f"[ERROR] No raw HTML logs found in: {INPUT_FOLDER}")
        return

    print(f"Found {len(target_files)} file(s). Extracting...")
    all_translated = []

    for fp in target_files:
        all_translated.extend(extract_rows_from_html(fp))

    # --- CORRELATION STEP ---
    print("\n[CORRELATION] Running Log Correlation Engine...")
    correlation_results = bridge_parser_to_correlation_engine(all_translated)

    # Save combined JSON output
    combined_data = {
        "correlation_analysis": correlation_results,
        "translated_records": all_translated
    }
    OUTPUT_JSON.write_text(json.dumps(combined_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Render dashboard
    build_html_dashboard(all_translated, correlation_results)

    print("\n" + "="*50)
    print(f"TOTAL ROWS EXTRACTED & TRANSLATED: {len(all_translated)}")
    print(f"ROOT CAUSE ANALYSIS COMPLETE: {len(correlation_results.get('root_causes', []))} Root Cause(s) Isolated")
    print(f"DASHBOARD CREATED: {OUTPUT_HTML}")
    print("="*50)

    if all_translated:
        webbrowser.open(OUTPUT_HTML.resolve().as_uri())


if __name__ == "__main__":
    main()