# Correlator code to be added by teammates
# fdm_cross_node_engine.py
import json

class FDMCrossNodeCorrelationEngine:
    def __init__(self):
        # 3-Node Architecture: Node A (FMS Primary), Node B (Avionics Bus Hub), Node C (GPS/Navigation Unit)
        self.cross_node_knowledge_base = {
            "PARKING_GROUND": {
                "phase_id": 1,
                "phase_name": "Parking & Ground Boot Phase",
                "trigger_node": "Node A (FMS Primary)",
                "predicted_what_can_happen": "Minor power bus fluctuations during initial boot can introduce synchronization delays across secondary nodes.",
                "actual_what_happened": "Serial No 81 logs confirm normal pre-check boot sequence initialized successfully at 09:41:22 AM across all nodes with zero active faults.",
                "node_reactions": {
                    "node_a_fms": "Initialized successfully; baseline power stable at 36°C module temperature.",
                    "node_b_avionics_bus": "Standby mode active; monitoring primary bus line with 0ms latency.",
                    "node_c_gps_nav": "Cold standby; awaiting ephemeris data upload from ground station."
                }
            },
            "ASCENT_CLIMB": {
                "phase_id": 2,
                "phase_name": "Ascent / Climb (Root Trigger Node)",
                "trigger_node": "Node A (FMS Primary)",
                "predicted_what_can_happen": "Unsynchronized repository data requests during rapid climb will trigger memory access blocks and force secondary channel fallback.",
                "actual_what_happened": "Fault Code 6074 triggered ('FMS Data Repository Access Failure') in Node A. This is the absolute Originating Root Cause.",
                "node_reactions": {
                    "node_a_fms": "CRITICAL FAULT CODE 6074: Primary software thread blocked reading repository memory.",
                    "node_b_avionics_bus": "Detected bus timeout (Thunderbolt fault); attempted automatic re-routing but failed due to memory lock.",
                    "node_c_gps_nav": "Unaffected directly, but holding previous vertical speed vector awaiting clean FMS sync."
                }
            },
            "CRUISE": {
                "phase_id": 3,
                "phase_name": "Cruise Phase (Cascading Instability)",
                "trigger_node": "Node B (Avionics Bus Hub)",
                "predicted_what_can_happen": "Memory addresses will overflow due to uninitialized float reads (-1.55e21), causing opposite channel bus flapping and single-mode degradation.",
                "actual_what_happened": "Memory address 2050 uninitialized read overflow detected alongside rapid 1-second cross-channel bus synchronization flip-flop.",
                "node_reactions": {
                    "node_a_fms": "Dual mode degraded to Single mode; opposite channel status reported as Unstable.",
                    "node_b_avionics_bus": "Bus flapping active; continuous re-transmission requests overloading buffer stack.",
                    "node_c_gps_nav": "Experiencing minor clock drift due to interrupted polling cycles from Node B."
                }
            },
            "DESCENT_APPROACH": {
                "phase_id": 4,
                "phase_name": "Descent & Approach (Endpoint Manifestation)",
                "trigger_node": "Node C (GPS/Navigation Unit)",
                "predicted_what_can_happen": "Cumulative timing jitter will manifest as a complete GPS receiver position drop and barometric altitude sensor freeze during final touchdown.",
                "actual_what_happened": "GPS Receiver Cold Start Re-sync Reset drop occurred (0.000000 Lat/Lon) with barometric altitude sensor freeze at 2870.01 ft.",
                "node_reactions": {
                    "node_a_fms": "Issued FMS Service Restart command following total loss of valid position feedback.",
                    "node_b_avionics_bus": "Logged extended record exceptions; bus locked awaiting manual override.",
                    "node_c_gps_nav": "ENDPOINT FAILURE: Receiver lost satellite lock; coordinates reset to 0.000000 and baro sensor frozen."
                }
            }
        }

    def get_full_cross_node_payload(self):
        return {
            "engine_title": "3-Node Cross-Node Correlation & Incident Narrative Engine",
            "nodes_monitored": ["Node A (FMS Primary)", "Node B (Avionics Bus Hub)", "Node C (GPS/Navigation Unit)"],
            "phases": self.cross_node_knowledge_base
        }

    def export_json(self):
        from .config import DATA_DIR
        payload = self.get_full_cross_node_payload()
        out_path = DATA_DIR / "fdm_cross_node_output.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Successfully generated '{out_path}' with 3-Node cross reactions!")

if __name__ == "__main__":
    engine = FDMCrossNodeCorrelationEngine()
    engine.export_json()
    
    data = engine.get_full_cross_node_payload()
    print("\n--- 3-NODE CROSS-CORRECTION PREVIEW ---")
    for key, val in data["phases"].items():
        print(f"\n[{val['phase_name']}] (Trigger: {val['trigger_node']})")
        print(f"  * PREDICTED : {val['predicted_what_can_happen']}")
        print(f"  * ACTUAL    : {val['actual_what_happened']}")
        print("  * INDEPENDENT NODE REACTIONS:")
        for node, reaction in val["node_reactions"].items():
            print(f"     - {node.upper()}: {reaction}")